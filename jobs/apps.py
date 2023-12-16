import json
import logging
from typing import Any, Dict, List
from http import HTTPStatus

import pika
from django.apps import AppConfig

from scrutiny.env import deploy_env, get_rmq_dsn  # noqa


class Publisher:
    def __init__(self):
        self.connected = False
        self.connection = None
        self.channel = None
        self.env = deploy_env()
        self.params = pika.URLParameters(get_rmq_dsn())
        self.topics: List[str] = []

    def connect(self):
        if self.connected or self.env == "test":
            return

        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()
        self.connected = True

    def on_close(self):
        if self.connected:
            self.connection.close()

    def queue_declare(self, topic: str):
        if topic not in self.topics and self.connected:
            self.channel.queue_declare(queue=topic, auto_delete=True)
            self.topics.append(topic)

    def publish(self, topic: str, msg: Dict[str, Any]):
        if self.connected:
            self.channel.basic_publish(
                exchange="",
                routing_key=topic,
                body=json.dumps(msg).encode(),
            )


publisher = Publisher()


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"

    def ready(self):
        from .signals import on_news_item_save  # noqa

        publisher.connect()


def broadcast(topic: str, msg: Dict[str, Any]):
    if publisher:
        publisher.queue_declare(topic)

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if publisher and result.status_code < HTTPStatus.BAD_REQUEST:
                try:
                    publisher.publish(topic, msg)
                except Exception:
                    logging.exception("not able to publish message")
            return result

        return wrapper

    return decorator
