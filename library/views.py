import logging
from typing import Any, List

import requests
from django.contrib.auth import mixins as auth
from django.views import generic
from opentelemetry import trace

from library.models import Article
from scrutiny.env import get_pocket_consumer_key
from scrutiny.views import ScrutinyListView


logger = logging.getLogger(__name__)
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

    def _get_page_context(self, *args, **kwargs):
        page = int(self.request.GET.get("next", 1))
        search = self.request.GET.get("search", None)
        tag = self.request.GET.get("tag", None)
        return {
            "items": [],
            "tags": set(),
            "previous": page - 1 if page > 1 else 0,
            "next": page + 1,
            "page": page,
            "search": search,
            "tag": tag,
        }

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{__name__}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            user = self.request.user.social_auth.first()
            context |= self._get_page_context()
            data = {
                "consumer_key": get_pocket_consumer_key(),
                "access_token": user.extra_data.get("access_token", ""),
                "contentType": "article",
                "detailType": "complete",
                "search": context.get("search"),
                "tag": context.get("tag"),
                "count": 10,
                "offset": 0,  # zero based
            }
            data["offset"] = (data["count"] * context.get("page")) - data["count"]
            for item in self._parse_response(make_request(self.pocket_url, data)):
                context["items"].append(item)
                for _, value in item.get("tags", {}).items():
                    context["tags"].add(value.get("tag"))
            return context


def make_request(pocket_url, data):
    resp = requests.post(
        pocket_url, json=data, headers={"Content-Type": "application/json"}
    )
    resp.raise_for_status()
    return resp.json()
