from django.apps import AppConfig
from django.conf import settings


class HackernewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        if getattr(settings, "FEATURES", {}).get("SSE", False):
            from news.signals import dispatch_new_item  # noqa
