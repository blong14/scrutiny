from django.contrib.auth import mixins as auth
from django.http import Http404
from django.views import generic
from django.views.generic.edit import FormView

from .forms import NewsItemForm
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


class NewsItemFormView(auth.LoginRequiredMixin, FormView):
    form_class = NewsItemForm
    template_name = "news/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["selected"] = form.selected_title()
        feed = FeedRegistry.get(form.feed())
        if not feed:
            raise Http404("feed does not exist")
        return parse_feed(
            context, feed, parser=default_parser.parse
        )

    def form_valid(self, form):
        form.save_item(self.request.user)
        return self.render_to_response(self.get_context_data(form=form))
