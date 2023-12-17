import functools
import logging
import threading
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from django.apps import AppConfig

from scrutiny.env import deploy_env, get_rmq_dsn  # noqa


class Publisher(threading.Thread):
    def __init__(self, queue: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel: Optional[BlockingChannel] = None
        self.connection: Optional[BlockingConnection] = None
        self.params = pika.URLParameters(get_rmq_dsn())
        self.daemon = True
        self.is_running = False
        self.name = "Publisher"
        self.queue = queue

    def run(self):
        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, auto_delete=True)
        self.is_running = True

        while self.is_running:
            self.connection.process_data_events(time_limit=1)

    def _publish(self, message):
        if self.channel is not None:
            try:
                self.channel.basic_publish("", self.queue, body=message.encode())
            except Exception:
                logging.exception("not able to publish message")

    def publish(self, message):
        if self.connection is not None:
            self.connection.add_callback_threadsafe(
                functools.partial(self._publish, message)
            )

    def stop(self):
        self.is_running = False
        if self.connection is None:
            return
        # Wait until all the data events have been processed
        self.connection.process_data_events(time_limit=1)
        if self.connection.is_open:
            self.connection.close()


publisher: Optional[Publisher] = None


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"

    def ready(self):
        from .signals import on_news_item_save  # noqa

        if deploy_env() != "test":
            global publisher
            publisher = Publisher(queue="news-summary")  # noqa
            publisher.start()
