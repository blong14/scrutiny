import json
import logging
from http import HTTPStatus

import pika
from django.contrib import messages
from django.contrib.auth import mixins as auth
from django.http import Http404
from django.views import generic
from django.views.generic.edit import CreateView

from .apps import publisher
from .forms import NewsItemForm
from .models import FeedRegistry, default_parser, parse_feed


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/index.html"
    page_limit = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_id = self.request.GET.get("feed", "hackernews")
        feed = FeedRegistry.get(feed_id)
        if not feed:
            raise Http404("feed does not exist")
        context["feeds"] = {f.id: f.title for f in FeedRegistry.feeds()}
        context["selected_feed"] = feed_id
        context["feed"] = parse_feed(
            context, feed, parser=default_parser.parse, limit=self.page_limit
        )
        return context


class NewsListView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "news/list.html"
    page_limit = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_id = self.request.GET.get("feed", "hackernews")
        feed = FeedRegistry.get(feed_id)
        if not feed:
            raise Http404("feed does not exist")
        context["feeds"] = {f.id: f.title for f in FeedRegistry.feeds()}
        context["selected_feed"] = feed_id
        return parse_feed(
            context, feed, parser=default_parser.parse, limit=self.page_limit
        )


class NewsItemFormView(auth.LoginRequiredMixin, CreateView):
    form_class = NewsItemForm
    template_name = "news/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        feed = FeedRegistry.get(form.feed())
        if not feed:
            raise Http404("feed does not exist")
        context["feeds"] = {f.id: f.title for f in FeedRegistry.feeds()}
        context["selected_feed"] = feed.id
        context["selected"] = form.selected_title()
        return parse_feed(context, feed)

    def form_valid(self, form: NewsItemForm):
        item = form.save(commit=False)
        item.user = self.request.user
        item.save()
        return self.render_to_response(self.get_context_data(form=form))


class NewsSummaryFormView(auth.LoginRequiredMixin, CreateView):
    form_class = NewsItemForm  # TODO: update this form
    template_name = "news/news_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = "Loading..."
        return context

    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        if publisher and resp.status_code < HTTPStatus.BAD_REQUEST:
            try:
                publisher.publish(
                    json.dumps({"topic": "news-summary", "action": "start"})
                )
            except pika.exceptions.ConnectionWrongStateError:
                logging.exception("news summary published failed - skipping")
                messages.error(request, "Ooops, not able to publish news summary.")
        return resp
