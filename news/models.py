from typing import List

from django.db import models
from django.urls import reverse


class Article(models.Model):
    """Article models a "story" from news
    Example:
        https://hacker-news.firebaseio.com/v0/item/8863.json
        {
            "by" : "dhouston",
            "descendants" : 71,
            "id" : 8863,
            "kids" : [ 8952, 9224, 8917, 8884, 8887, ... ],
            "score" : 111,
            "time" : 1175714200,
            "title" : "My YC app: Dropbox - Throw away your USB drive",
            "type" : "story",
            "url" : "http://www.getdropbox.com/u/2/screencast.html"
        }
    """

    class Meta:
        ordering = ["-time"]

    story_id = models.BigIntegerField()
    posted_by = models.CharField(max_length=256)
    score = models.IntegerField()
    slug = models.CharField(
        primary_key=True,
        max_length=36,
    )
    story_url = models.URLField()
    time = models.DateTimeField()
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def serializable_fields() -> List[str]:
        return [field.name for field in Article._meta.get_fields()]

    def get_absolute_url(self) -> str:
        return f"{reverse('news.list_view')}?slugs={str(self.slug)}"
