import datetime
import time

from django.utils.datetime_safe import new_datetime
from django.core.management.base import BaseCommand
from waitress import serve

from scrutiny.wsgi import application


class _Logger:
    def __init__(self, app, logger, style):
        self.application = app
        self.logger = logger
        self.style = style
        self.formatter = "[{time}] '{REQUEST_METHOD} {REQUEST_URI} {HTTP_VERSION}' {status} {duration}s"

    def __call__(self, environ, start_response):
        trace_start = time.perf_counter()
        start = new_datetime(datetime.datetime.now())

        def replacement_start_response(status, headers):
            duration = time.perf_counter() - trace_start
            self.write_log(environ, start, duration, status, self.style.HTTP_SUCCESS)
            return start_response(status, headers)

        return self.application(environ, replacement_start_response)

    def write_log(self, environ, start, duration, status, level):
        req_uri = f"{environ.get('SCRIPT_NAME', '')} {environ.get('PATH_INFO', '')}"
        if environ.get("QUERY_STRING"):
            req_uri = f"{req_uri}?{environ['QUERY_STRING']}"
        d = {
            "time": start,
            "REQUEST_METHOD": environ.get("REQUEST_METHOD"),
            "REQUEST_URI": req_uri,
            "HTTP_VERSION": environ.get("SERVER_PROTOCOL"),
            "status": status.split(None, 1)[0],
            "duration": f"{duration:0.3f}",
        }
        message = self.formatter.format(**d)
        self.logger.write(level(message))


def default_logger(*args, **kwargs) -> _Logger:
    return _Logger(*args, **kwargs)


class Command(BaseCommand):
    help = "Start WSGI Application Server"

    def add_arguments(self, parser) -> None:
        parser.add_argument("port", type=int, nargs="?", const=8080)

    def handle(self, *args, **options) -> None:
        try:
            self.stdout.write(self.style.SUCCESS("starting wsgi server"))
            serve(
                default_logger(application, self.stdout, self.style),
                port=options.get("port") or 8080,
            )
        except Exception as e:
            self.stderr.write(e)
        finally:
            self.stdout.write(self.style.SUCCESS("wsgi server stopped"))
