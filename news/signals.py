import json

from django.http import HttpRequest
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from opentelemetry import trace

from news.models import Event, Item
from news.views import NewsApiDashboardView, NewsListView


tracer = trace.get_tracer(__name__)


@receiver(post_save, sender=Item)
def dispatch_update_news_dashboard(sender: Item, **kwargs) -> None:
    with tracer.start_as_current_span(f"{__name__}.dispatch_update_news_dashboard"):
        instance = kwargs.pop("instance", Item())
        if instance.is_comment:
            return
        context = NewsApiDashboardView().get_context_data()
        with tracer.start_as_current_span(f"{__name__}.render_to_string"):
            msg = render_to_string("news/_dashboard.turbo.html", context=context)
        data = json.dumps({"target": "news", "topic": ["news"], "data": msg})
        Event(event_type="STORY_ADDED", event_data=data).save()


@receiver(post_save, sender=Item)
def dispatch_new_item(sender: Item, **kwargs) -> None:
    with tracer.start_as_current_span(f"{__name__}.dispatch_new_item"):
        instance = kwargs.pop("instance", sender)
        if instance.is_comment:
            return
        view = NewsListView()
        view.setup(request=HttpRequest())
        query = view.get_queryset()
        context = view.get_context_data(object_list=query)
        with tracer.start_as_current_span(f"{__name__}.render_to_string"):
            msg = render_to_string("news/_list.turbo.html", context=context)
        data = json.dumps({"target": "news", "topic": ["news"], "data": msg})
        Event(event_type="STORY_ADDED", event_data=data).save()
