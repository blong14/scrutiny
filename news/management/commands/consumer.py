import json
import logging
from typing import List, Optional
from urllib import parse

import requests
from django.core.management.base import BaseCommand
from django.http import HttpRequest

from news.models import Event
from news.views import EventListView
from scrutiny import env


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start Consuming News items created events"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("consuming..."))
        events = self._read()
        self._dispatch(events)
        self.stdout.write(self.style.SUCCESS("finished consuming."))

    def _read(self) -> List[Event]:
        view = EventListView()
        view.setup(request=HttpRequest())
        query = view.get_queryset()
        return [
            item for item in view.get_context_data(object_list=query).get("items", [])
        ]

    @staticmethod
    def _dispatch(events: List[Event]):
        token = env.get_mercure_token()
        if not token:
            raise EnvironmentError("missing jwt publish token")
        logger.info(len(events))
        for event in events:
            resp: Optional[requests.models.Response] = None
            try:
                resp = requests.post(
                    env.get_mercure_url(),
                    data=parse.urlencode(
                        json.loads(event.event_data),
                        True,
                    ),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    verify=False,
                )
            except Exception as e:
                logger.error("unknown error %s when sending for %s", e, events)
            if resp and resp.status_code != 200:
                logger.error("error dispatching event %s for %s", resp, events)
            logger.info(resp.status_code)
