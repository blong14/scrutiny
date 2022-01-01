from typing import List

from django.db import models
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

    def get_absolute_url(self) -> str:
        return reverse("jobs_api.update_view", args=[str(self.name)])
