import logging
from typing import Any, List

import requests
from django.contrib.auth import mixins as auth
from django.views import generic
from opentelemetry import trace

from library.models import Article
from scrutiny.env import get_pocket_consumer_key
from scrutiny.views import ScrutinyListView


tracer = trace.get_tracer(__name__)


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "library/index.html"


class PocketListView(auth.LoginRequiredMixin, ScrutinyListView):
    model = Article
    pocket_url = "https://getpocket.com/v3/get"
    template_name = "library/list.html"

    @staticmethod
    def _parse_response(resp) -> List[Any]:
        items: List[Any] = []
        try:
            items = [item for _, item in resp.get("list", {}).items()]
        except AttributeError as e:
            logging.warning(e)
        return items

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{__name__}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            user = self.request.user.social_auth.first()
            data = {
                "consumer_key": get_pocket_consumer_key(),
                "access_token": user.extra_data.get("access_token", ""),
                "contentType": "article",
                "detailType": "complete",
                "count": 10,
                "offset": 0,  # zero based
            }
            page = int(self.request.GET.get("next", 1))
            data["offset"] = (data["count"] * page) - data["count"]
            resp = requests.post(
                self.pocket_url, json=data, headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            items = self._parse_response(resp.json())
            context["items"] = items
            context["previous"] = page - 1 if page > 1 else 0
            context["next"] = page + 1
            return context
