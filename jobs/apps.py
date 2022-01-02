from django.apps import AppConfig
from django.conf import settings


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"

    def ready(self):
        if getattr(settings, "SSE", False):
            from jobs.signals import (  # noqa
                dispatch_update_jobs_dashboard,
            )
