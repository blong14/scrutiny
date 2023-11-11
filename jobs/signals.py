import logging

import requests
from requests.exceptions import HTTPError
from django.db.models.signals import post_save
from django.dispatch import receiver

from library.models import Article  # noqa
from news.models import NewsItem  # noqa
from scrutiny.env import get_pocket_consumer_key  # noqa


@receiver(post_save, sender=NewsItem)
def on_news_item_save(sender, **kwargs):
    instance = kwargs.get("instance")
    social_usr = instance.user.social_auth.first()
    access_token = social_usr.extra_data.get("access_token", "") if social_usr else ""
    try:
        resp = requests.post(
            "https://getpocket.com/v3/add",
            json={
                "consumer_key": get_pocket_consumer_key(),
                "access_token": access_token,
                "title": instance.title,
                "url": instance.url,
            },
        )
        resp.raise_for_status()
    except HTTPError:
        logging.exception("not able to save to pocket")
    else:
        item = resp.json().get("item")
        Article(
            id=int(item.get("item_id")),
            authors=item.get("authors", {}),
            excerpt=item.get("excerpt", ""),
            user=instance.user,
            listen_duration_estimate=0,
            resolved_title=item.get("title"),
        ).save()
