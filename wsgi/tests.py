from unittest import mock

from django.test import TestCase

from wsgi.management.commands.waitress import Command


class NoopLogger:
    pass


class TestWaitressCommand(TestCase):
    @mock.patch("wsgi.management.commands.waitress.default_logger")
    @mock.patch("wsgi.management.commands.waitress.serve")
    def test_handle(self, mock_serve, mock_logger):
        noop = NoopLogger()
        mock_logger.return_value = noop
        cmd = Command()
        cmd.handle()
        mock_serve.assert_called_with(
            noop,
            port=8080,
        )
