from django.conf import settings

from news.models import Article
from news.serializers import ArticleSerializer
from scrutiny.views import ScrutinyListView, ScrutinyApiListView


class NewsListView(ScrutinyListView):
    model = Article
    template_name = "news/list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["features"] = getattr(settings, "FEATURES", {})
        return context


class NewsApiListView(ScrutinyApiListView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
