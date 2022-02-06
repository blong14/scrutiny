import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class HackernewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"
