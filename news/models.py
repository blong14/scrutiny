import logging
from typing import List, Optional

from django.db import models
from django.urls import reverse


logger = logging.getLogger(__name__)


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
        get_latest_by = "score"
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

    @staticmethod
    def max_score_article() -> Optional["Article"]:
        article_with_max = None
        try:
            article_with_max = Article.objects.latest("score")
        except Article.DoesNotExist as e:
            logger.error("unable to find max score %s", e)
        return article_with_max

    def get_absolute_url(self) -> str:
        return f"{reverse('news.list_view')}?slugs={str(self.slug)}"
