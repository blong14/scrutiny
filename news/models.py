import logging
from typing import List, Optional

from django.db import models
from django.urls import reverse


logger = logging.getLogger(__name__)


class Item(models.Model):
    """Item models an "item" from news algolia search API
    Example:
        https://hn.algolia.com/api
        {
            id: 1,
            created_at: "2006-10-09T18:21:51.000Z",
            author: "pg",
            title: "Y Combinator",
            url: "http://ycombinator.com",
            text: null,
            points: 57,
            parent_id: null,
            children: [
                {
                    id: 2,
                    created_at: "2006-10-09T18:21:51.000Z",
                    author: "pg",
                    title: "Y Combinator",
                    url: "http://ycombinator.com",
                    text: null,
                    points: 57,
                    parent_id: 1,
                    children: []
                },
            ]
        }
    """

    ITEM_TYPES = (
        ("STORY", "story"),
        ("COMMENT", "comment"),
    )

    class Meta:
        get_latest_by = "points"
        ordering = ["-added_at"]

    id = models.BigAutoField(primary_key=True, serialize=True)
    author = models.CharField(max_length=256)
    parent = models.ForeignKey(
        to="Item", on_delete=models.CASCADE, null=True, related_name="children"
    )
    points = models.IntegerField()
    slug = models.CharField(max_length=36)
    text = models.TextField(null=True, default="")
    title = models.CharField(max_length=256)
    type = models.CharField(choices=ITEM_TYPES, default="STORY", max_length=32)
    url = models.URLField()
    created_at = models.DateTimeField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def serializable_fields() -> List[str]:
        return [field.name for field in Item._meta.get_fields()]

    @staticmethod
    def max_score_item() -> Optional["Item"]:
        item_with_max = None
        try:
            item_with_max = Item.objects.latest("points")
        except Item.DoesNotExist as e:
            logger.error("unable to find max score %s", e)
        return item_with_max

    def get_absolute_url(self) -> str:
        return f"{reverse('news.list_view')}?slugs={str(self.slug)}"
