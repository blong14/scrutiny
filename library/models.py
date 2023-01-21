import uuid

from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):

    id = models.BigAutoField(primary_key=True)
    value = models.CharField(max_length=256)
    user = models.ForeignKey(User, related_name="tags", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.value  # noqa


class Article(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True)
    authors = models.JSONField()
    excerpt = models.TextField(default="")
    slug = models.UUIDField(default=uuid.uuid4, editable=False)
    resolved_title = models.CharField(max_length=256)
    listen_duration_estimate = models.IntegerField()
    tags = models.ManyToManyField(Tag)
    user = models.ForeignKey(User, related_name="articles", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobEvent(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
