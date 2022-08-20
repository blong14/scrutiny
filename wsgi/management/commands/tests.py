from datetime import datetime, timedelta
from unittest import mock

from django.test import TestCase

from .waitress import IOWrapper, Logger


class TestLogger(TestCase):
    def test_write(self):
        # given
        io_mock = mock.Mock(spec=IOWrapper)
        duration = 50.0
        start = datetime.utcnow()
        logger = Logger(stdout=io_mock, style=mock.Mock())

        # when
        logger.write(dict(), start, duration, "ok")

        # then
        io_mock.write.assert_called_once()
