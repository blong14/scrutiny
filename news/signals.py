import logging
from typing import Optional
from urllib import parse

import requests
from django.conf import settings
from django.http import HttpRequest
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from opentelemetry import trace

from news.models import Item
from news.views import NewsApiDashboardView, NewsListView


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
module = "news.signals"


def _send(sender: Item, msg: str):
    token = settings.JWT_PUBLISH_TOKEN
    if not token:
        raise EnvironmentError("missing jwt publish token")
    resp: Optional[requests.models.Response] = None
    try:
        resp = requests.post(
            settings.MERCURE_URL,
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
    if resp and resp.status_code != 200:
        logger.error("error dispatching event %s for %s", resp, sender)


@receiver(post_save, sender=Item)
def dispatch_update_news_dashboard(sender: Item, **kwargs) -> None:
    with tracer.start_as_current_span(f"{module}.dispatch_update_news_dashboard"):
        instance = kwargs.pop("instance", Item())
        if instance.is_comment:
            return
        context = NewsApiDashboardView().get_context_data()
        with tracer.start_as_current_span(f"{module}.render_to_string"):
            msg = render_to_string("news/_dashboard.turbo.html", context=context)
        with tracer.start_as_current_span(f"{module}._send"):
            _send(sender, msg)


@receiver(post_save, sender=Item)
def dispatch_new_item(sender: Item, **kwargs) -> None:
    with tracer.start_as_current_span(f"{module}.dispatch_new_item"):
        instance = kwargs.pop("instance", Item())
        if instance.is_comment:
            return
        view = NewsListView()
        view.setup(request=HttpRequest())
        query = view.get_queryset()
        context = view.get_context_data(object_list=query)
        with tracer.start_as_current_span(f"{module}.render_to_string"):
            msg = render_to_string("news/_list.turbo.html", context=context)
        with tracer.start_as_current_span(f"{module}._send"):
            _send(sender, msg)
