import uuid

from django.db import models


class Project(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True, serialize=True)
    slug = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Note(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True, serialize=True)
    slug = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    body = models.TextField()
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE, null=True, related_name="notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
