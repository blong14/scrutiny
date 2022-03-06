from django.contrib.auth import mixins as auth
from django.http import Http404
from django.views import generic

from .models import FeedRegistry, default_parser, parse_feed


class NewsListView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = [f.id for f in FeedRegistry.feeds()]
        return context


class NewsFeedView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/feed.html"
    page_limit = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed = FeedRegistry.get(self.request.GET.get("feed", ""))
        if not feed:
            raise Http404("feed does not exist")
        return parse_feed(
            context, feed, parser=default_parser.parse, limit=self.page_limit
        )
