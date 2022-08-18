import logging
import time
from typing import Callable

from django.core.management.base import BaseCommand
from django.utils.timezone import now as utc_now

from waitress import serve

from scrutiny.wsgi import application


logger = logging.getLogger(__name__)


def _request_info(environ):
    req_uri = f"{environ.get('SCRIPT_NAME', '')} {environ.get('PATH_INFO', '')}"
    if environ.get("QUERY_STRING"):
        req_uri = f"{req_uri}?{environ['QUERY_STRING']}"
    return environ.get("SERVER_PROTOCOL"), environ.get("REQUEST_METHOD"), req_uri


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
    return _LoggingApplication(application, *args, **kwargs)


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
