import uuid

from django.db import models


class Article(models.Model):
    class Meta:
        ordering = ["created_at"]

    description = models.TextField(default="")
    slug = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
