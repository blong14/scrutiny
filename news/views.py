import requests
from django.contrib.auth import mixins as auth
from django.http import Http404
from django.views import generic
from django.views.generic.edit import FormView

from library.models import Article
from scrutiny.env import get_pocket_consumer_key

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
    remote_url = "https://getpocket.com/v3/add"
    template_name = "news/list.html"

    def access_token(self):
        social_user = self.request.user.social_auth.first()
        if social_user is None:
            return ""
        return social_user.extra_data.get("access_token", "")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["selected"] = form.selected_title()
        feed = FeedRegistry.get(form.feed())
        if not feed:
            raise Http404("feed does not exist")
        return parse_feed(context, feed)

    def form_valid(self, form: NewsItemForm):
        resp = requests.post(
            self.remote_url,
            json={
                "consumer_key": get_pocket_consumer_key(),
                "access_token": self.access_token(),
                "title": form.selected_title(),
                "url": form.get_url(),
            },
        )
        resp.raise_for_status()
        self.save_item(resp.json().get("item"))
        return self.render_to_response(
            self.get_context_data(form=form),
        )

    def save_item(self, item):
        Article(
            id=int(item.get("item_id")),
            authors=item.get("authors", {}),
            excerpt=item.get("excerpt", ""),
            user=self.request.user,
            listen_duration_estimate=0,
            resolved_title=item.get("title"),
        ).save()
