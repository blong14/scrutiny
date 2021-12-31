from django.db import models


class Feature(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
