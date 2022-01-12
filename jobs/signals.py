import logging
from typing import Optional
from urllib import parse

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest
from django.template.loader import render_to_string
from opentelemetry import trace

from jobs.models import Job
from jobs.views import JobsStatusView


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
module = "jobs.signals"


def _send(sender: Job, msg: str):
    token = settings.JWT_PUBLISH_TOKEN
    if not token:
        raise EnvironmentError("missing jwt publish token")
    resp: Optional[requests.models.Response] = None
    try:
        resp = requests.post(
            settings.MERCURE_URL,
            data=parse.urlencode(
                {"target": "news", "topic": ["news"], "data": msg}, True
            ),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            verify=False,
        )
    except Exception as e:
        logger.error("unknown error %s when sending for %s", e, sender)
    if resp and resp.status_code != 200:
        logger.error("error dispatching event %s for %s", resp, sender)


@receiver(post_save, sender=Job)
def dispatch_update_jobs_dashboard(sender: Job, **kwargs) -> None:
    with tracer.start_as_current_span(f"{module}.dispatch_update_jobs_dashboard"):
        view = JobsStatusView()
        view.setup(request=HttpRequest())
        context = view.get_context_data(name="hackernews")
        with tracer.start_as_current_span(f"{module}.render_to_string"):
            msg = render_to_string("jobs/_dashboard.turbo.html", context=context)
        with tracer.start_as_current_span(f"{module}._send"):
            _send(sender, msg)
