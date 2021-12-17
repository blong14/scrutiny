import logging
from urllib import parse

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from news.models import Article


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def dispatch_new_item(sender, **kwargs) -> None:
    logger.info("sending new article")
    token = settings.JWT_PUBLISH_TOKEN
    if not token:
        raise EnvironmentError("missing jwt publish token")
    item = kwargs.get("instance", None)
    if not item:
        raise ValueError(f"invalid instance of {sender}")
    event = render_to_string("news/new_item.html", context={"item": item})
    try:
        resp = requests.post(
            "https://caddy:8081/.well-known/mercure",
            data=parse.urlencode(
                {"target": "news", "topic": ["news"], "data": event}, True
            ),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            verify=False,
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
    except Exception as e:
        logger.error("uknown error %s", e)
    finally:
        logger.info("finished sending new article")
