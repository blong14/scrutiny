from unittest import mock

from django.test import TestCase

from wsgi.management.commands.waitress import Command, _LoggingApplication


class TestWaitressCommand(TestCase):
    @mock.patch("wsgi.management.commands.waitress.default_application")
    @mock.patch("wsgi.management.commands.waitress.serve")
    def test_handle(self, mock_serve, mock_wsgi):
        noop = mock.Mock(spec=_LoggingApplication)
        mock_wsgi.return_value = noop
        cmd = Command()
        cmd.handle()
        mock_serve.assert_called_with(noop, port=8080)
