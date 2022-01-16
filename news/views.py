import datetime
import logging
from typing import List, Tuple, Union

from django.conf import settings
from django.contrib.auth import mixins as auth
from django.utils.datetime_safe import new_datetime
from django.views import generic
from opentelemetry import trace
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from news.models import Item
from news.serializers import ItemSerializer


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
module = "news.views"


class NewsApiDashboardView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/dashboard.html"
    module = f"{module}.NewsApiDashboardView"

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            now = datetime.datetime.now()
            item = Item.max_score_item()
            context["max_score"] = item.points if item else 0
            context["max_score_slug"] = item.slug if item else ""
            with tracer.start_as_current_span(f"{self.module}.Items.count"):
                context["total"] = Item.objects.filter(type="STORY").count()
            with tracer.start_as_current_span(f"{self.module}.Items.new_today"):
                context["new_today"] = Item.objects.filter(
                    type="STORY", added_at__gte=new_datetime(now).date()
                ).count()
            return context


class NewsListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Item
    module = f"{module}.NewsListView"
    paginate_by = 10
    order = ["-created_at"]
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
    queryset = Item.objects.prefetch_related("children").filter(parent=None)
    serializer_class = ItemSerializer

    @staticmethod
    def _parse_request(
        request, many: bool = False
    ) -> Tuple[Union[dict, List[dict]], List[dict]]:
        if not many:
            return request.data, []
        parents, children = [], []
        for item in request.data:
            _type = item.get("type")
            if _type == "STORY":
                parents.append(item)
            elif _type == "COMMENT":
                children.append(item)
        return parents, children

    def perform_create(self, serializer):
        with tracer.start_as_current_span(f"{self.module}.perform_create"):
            super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.create"):
            many = True if isinstance(request.data, list) else False
            with tracer.start_as_current_span(f"{self.module}._parse_request"):
                parents, children = self._parse_request(request, many=many)
            parent_serializer = self.get_serializer(data=parents, many=many)
            parent_serializer.is_valid(raise_exception=True)
            self.perform_create(parent_serializer)
            if children:
                children_serializer = self.get_serializer(data=children, many=many)
                children_serializer.is_valid(raise_exception=True)
                self.perform_create(children_serializer)
            headers = self.get_success_headers(parent_serializer.data)
            return Response(parent_serializer.data, status=201, headers=headers)
