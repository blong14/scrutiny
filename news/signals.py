import logging
from typing import Optional
from urllib import parse

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from news.models import Article
from news.views import NewsApiDashboardView


logger = logging.getLogger(__name__)


def _send(sender: Article, msg: str):
    token = settings.JWT_PUBLISH_TOKEN
    if not token:
        raise EnvironmentError("missing jwt publish token")
    resp: Optional[requests.models.Response] = None
    try:
        resp = requests.post(
            "https://scrutiny.local:8081/.well-known/mercure",
            data=parse.urlencode(
                {"target": "news", "topic": ["news"], "data": msg}, True
            ),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            verify=False,
        )
    except Exception as e:
        logger.error("unknown error %s when sending for %s", e, sender)
    if resp.status_code != 200:
        logger.error("error dispatching event %s for %s", resp, sender)


@receiver(post_save, sender=Article)
def dispatch_update_dashboard(sender: Article, **kwargs) -> None:
    context = NewsApiDashboardView().get_context_data()
    msg = render_to_string("news/_dashboard.turbo.html", context=context)
    _send(sender, msg)


@receiver(post_save, sender=Article)
def dispatch_new_item(sender: Article, **kwargs) -> None:
    item = kwargs.get("instance", None)
    if not item:
        raise ValueError(f"invalid instance of {sender}")
    msg = render_to_string("news/_list_item.turbo.html", context={"item": item})
    _send(sender, msg)
