from datetime import timedelta
from typing import List

from django.db import models
from django.utils.timezone import now as utc_now
from django.urls import reverse


class Job(models.Model):
    """Job models an asynchronous background job"""

    STATUS = (("Healthy", "Healthy"), ("Degraded", "Degraded"))

    name = models.SlugField(db_index=True, max_length=36, primary_key=True)
    status = models.CharField(choices=STATUS, default="Healthy", max_length=32)
    synced_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def serializable_fields() -> List[str]:
        return [field.name for field in Job._meta.get_fields()]

    @property
    def active(self) -> bool:
        when = utc_now() - self.synced_at
        return when < timedelta(minutes=1)

    def get_absolute_url(self) -> str:
        return reverse("jobs_api.update_view", args=[str(self.name)])
