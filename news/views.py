import datetime
import logging

from django.utils.datetime_safe import new_datetime

from news.models import Item
from news.serializers import ItemSerializer
from scrutiny.views import ScrutinyApiListView, ScrutinyListView, ScrutinyTemplateView


logger = logging.getLogger(__name__)


class NewsApiDashboardView(ScrutinyTemplateView):
    template_name = "news/_dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        now = datetime.datetime.now()
        item = Item.max_score_item()
        context["max_score"] = item.points if item else 0
        context["max_score_slug"] = item.slug if item else ""
        context["total"] = Item.objects.count()
        context["new_today"] = Item.objects.filter(
            added_at__gte=new_datetime(now).date()
        ).count()
        return context


class NewsListView(ScrutinyListView):
    model = Item
    order = ["-created_at"]
    template_name = "news/list.html"

    def get_queryset(self):
        query = self.model.objects.filter(parent_id=None)
        slugs = self.request.GET.get("slugs")
        if slugs:
            query = query.filter(pk__in=[slug for slug in slugs.split(",")])
        query = query.order_by(*self.order)
        return query


class NewsApiListView(ScrutinyApiListView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
