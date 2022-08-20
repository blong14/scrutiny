import time
from typing import Callable

from django.core.management.base import BaseCommand
from django.utils.timezone import now as utc_now

from waitress import serve

from scrutiny.wsgi import application


def _request_info(environ):
    req_uri = f"{environ.get('SCRIPT_NAME', '')} {environ.get('PATH_INFO', '')}"
    if environ.get("QUERY_STRING"):
        req_uri = f"{req_uri}?{environ['QUERY_STRING']}"
    return environ.get("SERVER_PROTOCOL"), environ.get("REQUEST_METHOD"), req_uri


class Logger:
    def __init__(self, stdout, style):
        self.formatter = "[{time}] '{REQUEST_METHOD} {REQUEST_URI} {HTTP_VERSION}' {status} {duration}s"
        self.stdout = stdout
        self.style = style
        self.success = self.style.HTTP_SUCCESS

    def write(self, environ, start, duration, status):
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
        self.stdout.write(self.success(message))


class _LoggingApplication:
    def __init__(self, wsgi, lgr: Logger):
        self.application = wsgi
        self.logger = lgr

    def __call__(self, environ, start_response):
        trace_start = time.perf_counter()
        start = utc_now()

        def replacement_start_response(status, headers):
            duration = time.perf_counter() - trace_start
            self.logger.write(environ, start, duration, status)
            return start_response(status, headers)

        return self.application(environ, replacement_start_response)


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
                default_application(Logger(self.stdout, self.style)),
                port=options.get("port") or 8080,
            )
        except Exception as e:
            self.stderr.write(e)
        finally:
            self.stdout.write(self.style.SUCCESS("wsgi server stopped"))
