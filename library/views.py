import requests
from django.conf import settings
from django.contrib.auth import mixins as auth
from opentelemetry import trace

from library.models import Article
from scrutiny.views import ScrutinyListView


tracer = trace.get_tracer(__name__)


class PocketListView(auth.LoginRequiredMixin, ScrutinyListView):
    model = Article
    pocket_url = "https://getpocket.com/v3/get"
    template_name = "library/list.html"

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{__name__}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            consumer_key = getattr(settings, "SOCIAL_AUTH_POCKET_KEY", "")
            user = self.request.user.social_auth.first()
            data = {
                "consumer_key": consumer_key,
                "access_token": user.extra_data.get("access_token", ""),
                "contentType": "article",
                "detailType": "complete",
                "count": 10,
            }
            resp = requests.post(
                self.pocket_url, json=data, headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            context["items"] = [item for _, item in resp.json()["list"].items()]
            return context
