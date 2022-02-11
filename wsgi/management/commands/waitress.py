import functools
import logging
import time
from typing import Callable

from django.core.management.base import BaseCommand
from django.utils.timezone import now as utc_now
from opentelemetry import context, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.wsgi import (
    OpenTelemetryMiddleware,
    collect_request_attributes,
    get_default_span_name,
    wsgi_getter,
)
from opentelemetry.propagate import extract
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.status import Status, StatusCode

from waitress import serve

from scrutiny import env
from scrutiny.wsgi import application


logger = logging.getLogger(__name__)
provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: "scrutiny-http-service"})
)
trace.set_tracer_provider(provider)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        if env.should_trace()
        else InMemorySpanExporter(),
    )
)


def _default_span_name(environ):
    _, _, uri = _request_info(environ)
    return f"{get_default_span_name(environ)} {uri}"


def _request_info(environ):
    req_uri = f"{environ.get('SCRIPT_NAME', '')} {environ.get('PATH_INFO', '')}"
    if environ.get("QUERY_STRING"):
        req_uri = f"{req_uri}?{environ['QUERY_STRING']}"
    return environ.get("SERVER_PROTOCOL"), environ.get("REQUEST_METHOD"), req_uri


# Put this in a sub function to not delay the call to the wrapped
# WSGI application (instrumentation should change the application
# behavior as little as possible).
def _end_span_after_iterating(iterable, span, token):
    try:
        with trace.use_span(span):
            yield from iterable
    finally:
        close = getattr(iterable, "close", None)
        if close:
            close()
        span.end()
        context.detach(token)


class _TracingApplication(OpenTelemetryMiddleware):
    def __call__(self, environ, start_response):
        """The WSGI application
        Args:
            environ: A WSGI environment.
            start_response: The WSGI start_response callable.
        """
        token = context.attach(extract(environ, getter=wsgi_getter))
        _, method, uri = _request_info(environ)
        span = self.tracer.start_span(
            _default_span_name(environ),
            kind=trace.SpanKind.SERVER,
            attributes=collect_request_attributes(environ),
        )
        if self.request_hook:
            self.request_hook(span, environ)
        response_hook = self.response_hook
        if response_hook:
            response_hook = functools.partial(response_hook, span, environ)
        try:
            with trace.use_span(span):
                start_response = self._create_start_response(
                    span, start_response, response_hook
                )
                iterable = self.wsgi(environ, start_response)
                return _end_span_after_iterating(iterable, span, token)
        except Exception as ex:
            if span.is_recording():
                span.set_status(Status(StatusCode.ERROR, str(ex)))
            span.end()
            context.detach(token)
            raise


class _LoggingApplication:
    def __init__(self, wsgi, lgr, style):
        self.application = wsgi
        self.logger = lgr
        self.style = style
        self.formatter = "[{time}] '{REQUEST_METHOD} {REQUEST_URI} {HTTP_VERSION}' {status} {duration}s"

    def __call__(self, environ, start_response):
        trace_start = time.perf_counter()
        start = utc_now()

        def replacement_start_response(status, headers):
            duration = time.perf_counter() - trace_start
            self.write_log(environ, start, duration, status, self.style.HTTP_SUCCESS)
            return start_response(status, headers)

        return self.application(environ, replacement_start_response)

    def write_log(self, environ, start, duration, status, level):
        protocol, method, uri = _request_info(environ)
        d = {
            "time": start,
            "REQUEST_METHOD": method,
            "REQUEST_URI": uri,
            "HTTP_VERSION": protocol,
            "status": status.split(None, 1)[0],
            "duration": f"{duration:0.3f}",
        }
        message = self.formatter.format(**d)
        self.logger.write(level(message))


def default_application(*args, **kwargs) -> Callable:
    provider = trace.get_tracer_provider()
    return _TracingApplication(
        wsgi=_LoggingApplication(application, *args, **kwargs),
        tracer_provider=provider,
    )


class Command(BaseCommand):
    help = "Start WSGI Application Server"

    def add_arguments(self, parser) -> None:
        parser.add_argument("port", type=int, nargs="?", const=8080)

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("starting wsgi server"))
        try:
            serve(
                default_application(self.stdout, self.style),
                port=options.get("port") or 8080,
            )
        except Exception as e:
            self.stderr.write(e)
        finally:
            self.stdout.write(self.style.SUCCESS("wsgi server stopped"))
