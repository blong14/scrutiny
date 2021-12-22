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

    class Meta:
        get_latest_by = "points"
        ordering = ["-added_at"]

    id = models.BigIntegerField()
    author = models.CharField(max_length=256)
    parent_id = models.ForeignKey(to="Item", on_delete=models.CASCADE, null=True)
    points = models.IntegerField()
    slug = models.CharField(
        primary_key=True,
        max_length=36,
    )
    text = models.TextField(null=True, default="")
    title = models.CharField(max_length=256)
    url = models.URLField()
    created_at = models.DateTimeField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def serializable_fields() -> List[str]:
        return [
            field.name
            for field in Item._meta.get_fields()
            if field.name
            not in (
                "item",
                "text",
            )
        ]

    @staticmethod
    def optional_fields() -> List[str]:
        return [
            "text",
        ]

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
