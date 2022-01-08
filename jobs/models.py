from datetime import datetime, timedelta
from typing import List

from django.db import models
from django.urls import reverse
from opentelemetry import trace


tracer = trace.get_tracer(__name__)


class Job(models.Model):
    """Job models an asynchronous background job"""

    module = "jobs.serializers.Job"
    STATUS = (("Healthy", "Healthy"), ("Degraded", "Degraded"))

    name = models.SlugField(db_index=True, max_length=36, primary_key=True)
    status = models.CharField(choices=STATUS, default="Healthy", max_length=32)
    synced_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def serializable_fields() -> List[str]:
        with tracer.start_as_current_span(f"{Job.module}.serializable_fields"):
            return [field.name for field in Job._meta.get_fields()]

    @property
    def active(self) -> bool:
        with tracer.start_as_current_span(f"{self.module}.active"):
            when = datetime.utcnow() - self.synced_at
            return when < timedelta(minutes=1)

    def get_absolute_url(self) -> str:
        with tracer.start_as_current_span(f"{self.module}.get_absolute_url"):
            return reverse("jobs_api.update_view", args=[str(self.name)])
