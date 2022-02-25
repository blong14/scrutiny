import json
import logging

from django.conf import settings
from django.contrib.auth import mixins as auth
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.timezone import make_aware, now as utc_now
from django.views import generic
from opentelemetry import trace
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from news.models import Event, Item
from news.serializers import ItemSerializer


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
module = __name__


class EventListView(generic.ListView):
    context_object_name = "items"
    model = Event
    module = f"{module}.EventListView"
    order = ["-created_at"]

    def get_queryset(self):
        with tracer.start_as_current_span(f"{self.module}.get_query_set"):
            return self.model.objects.order_by(*self.order)[:10]


class NewsApiDashboardView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/dashboard.html"
    module = f"{module}.NewsApiDashboardView"

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            now = utc_now()
            item = Item.max_score_item()
            context["max_score"] = item.points if item else 0
            context["max_score_slug"] = item.slug if item else ""
            with tracer.start_as_current_span(f"{self.module}.Items.count"):
                context["total"] = Item.objects.filter(type="STORY").count()
            with tracer.start_as_current_span(f"{self.module}.Items.new_today"):
                context["new_today"] = Item.objects.filter(
                    type="STORY", added_at__gte=now.date()
                ).count()
            return context


class NewsListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Item
    module = f"{module}.NewsListView"
    paginate_by = 10
    order = ["-added_at"]
    template_name = "news/list.html"

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            context["sse"] = getattr(settings, "SSE", False)
            return context

    def get_queryset(self):
        with tracer.start_as_current_span(f"{self.module}.get_query_set"):
            query = self.model.objects.prefetch_related("children").filter(type="STORY")
            slugs = self.request.GET.get("slugs") if self.request else None
            if slugs:
                query = query.filter(slug__in=[slug for slug in slugs.split(",")])
            query = query.order_by(*self.order)
            return query


class NewsApiListView(ListCreateAPIView):
    module = f"{module}.NewsApiListView"
    queryset = (
        Item.objects.prefetch_related("children")
        .filter(parent=None)
        .order_by("-added_at")
    )
    serializer_class = ItemSerializer

    def perform_create(self, serializer):
        with tracer.start_as_current_span(f"{self.module}.perform_create"):
            super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.create"):
            many = True if isinstance(request.data, list) else False
            parent_serializer = self.get_serializer(data=request.data, many=many)
            parent_serializer.is_valid(raise_exception=True)
            self.perform_create(parent_serializer)
            if parent_serializer.instance and not parent_serializer.instance.is_comment:
                dispatch_new_item()
                dispatch_update_news_dashboard()
            headers = self.get_success_headers(parent_serializer.data)
            return Response(parent_serializer.data, status=201, headers=headers)


def dispatch_update_news_dashboard() -> None:
    with tracer.start_as_current_span(f"{__name__}.dispatch_update_news_dashboard"):
        context = NewsApiDashboardView().get_context_data()
        with tracer.start_as_current_span(f"{__name__}.render_to_string"):
            msg = render_to_string("news/_dashboard.turbo.html", context=context)
        data = json.dumps({"target": "news", "topic": ["news"], "data": msg})
        Event(event_type="STORY_ADDED", event_data=data).save()


def dispatch_new_item() -> None:
    with tracer.start_as_current_span(f"{__name__}.dispatch_new_item"):
        view = NewsListView()
        view.setup(request=HttpRequest())
        query = view.get_queryset()
        context = view.get_context_data(object_list=query)
        with tracer.start_as_current_span(f"{__name__}.render_to_string"):
            msg = render_to_string("news/_list.turbo.html", context=context)
        data = json.dumps({"target": "news", "topic": ["news"], "data": msg})
        Event(event_type="STORY_ADDED", event_data=data).save()