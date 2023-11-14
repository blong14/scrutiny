import datetime
import logging

import requests
from requests.exceptions import HTTPError
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

from library.models import Article  # noqa
from news.models import NewsItem  # noqa
from scrutiny.env import get_pocket_consumer_key  # noqa


@receiver(post_save, sender=NewsItem)
def on_news_item_save(sender, **kwargs):
    instance = kwargs.get("instance")
    if not instance:
        logging.error("signal triggered without instance")
        return

    if instance.status != "pending":
        logging.debug("skipping library update")
        return

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
        return

    item = resp.json().get("item")
    if item:
        try:
            Article(
                authors=item.get("authors", {}),
                created_at=datetime.datetime.now(),
                excerpt=item.get("excerpt", ""),
                id=int(item.get("item_id")),
                listen_duration_estimate=0,
                resolved_title=item.get("title"),
                user=instance.user,
            ).save()
        except ValidationError:
            logging.exception("not able to save article")
            instance.status = "error"
            return
        else:
            instance.status = "success"
    else:
        instance.status = "error"

    instance.save()
