from django.contrib.auth import mixins as auth
from django.http import Http404
from django.views import generic

from .models import FeedRegistry, default_parser, parse_feed


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/index.html"
    page_limit = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = {f.id: f.title for f in FeedRegistry.feeds()}
        feed = FeedRegistry.get(self.request.GET.get("feed", "hackernews"))
        context["feed"] = parse_feed(
            {}, feed, parser=default_parser.parse, limit=self.page_limit
        )
        return context


class NewsListView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/list.html"
    page_limit = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed = FeedRegistry.get(self.request.GET.get("feed", "hackernews"))
        if not feed:
            raise Http404("feed does not exist")
        return parse_feed(
            context, feed, parser=default_parser.parse, limit=self.page_limit
        )
