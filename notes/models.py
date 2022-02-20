from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Project(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True, serialize=True)
    slug = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    user = models.ForeignKey(User, related_name="user", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_absolute_url(self):
        return reverse("notes.detail_view", args=[self.slug])


class Note(models.Model):
    class Meta:
        ordering = ["created_at"]

    id = models.BigAutoField(primary_key=True, serialize=True)
    slug = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    body = models.TextField()
    project = models.ForeignKey(Project, related_name="notes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
