import datetime
import logging

from django.utils.datetime_safe import new_datetime

from news.models import Article
from news.serializers import ArticleSerializer
from scrutiny.views import ScrutinyApiListView, ScrutinyListView, ScrutinyTemplateView


logger = logging.getLogger(__name__)


class NewsApiDashboardView(ScrutinyTemplateView):
    template_name = "news/_dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        now = datetime.datetime.now()
        try:
            context["max_score"] = Article.objects.latest("score").score
        except Article.DoesNotExist as e:
            logger.error("unable to find max score %s", e)
            context["max_score"] = 0
        context["total"] = Article.objects.count()
        context["new_today"] = Article.objects.filter(
            created_at__gte=new_datetime(now).date()
        ).count()
        return context


class NewsListView(ScrutinyListView):
    model = Article
    order = ["-created_at"]
    template_name = "news/list.html"

    def get_queryset(self):
        query = self.model.objects.all()
        slugs = self.request.GET.get("slugs")
        if slugs:
            query = query.filter(pk__in=[slug for slug in slugs.split(",")])
        query = query.order_by(*self.order)
        return query


class NewsApiListView(ScrutinyApiListView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
