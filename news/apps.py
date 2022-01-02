import logging

from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class HackernewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        if getattr(settings, "SSE", False):
            from news.signals import (  # noqa
                dispatch_new_item,
                dispatch_update_news_dashboard,
            )
