import uuid

from django.db import models


class Project(models.Model):
    class Meta:
        ordering = ["created_at"]

    project_id = models.BigIntegerField()
    slug = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
