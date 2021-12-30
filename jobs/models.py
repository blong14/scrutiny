from django.db import models


class Job(models.Model):
    """Job models an asynchronous background job"""

    STATUS = (("Healthy", "Healthy"), ("Degraded", "Degraded"))

    name = models.CharField(max_length=64)
    status = models.CharField(choices=STATUS, default="Healthy", max_length=32)
    synced_at = models.DateTimeField(auto_now=True)
