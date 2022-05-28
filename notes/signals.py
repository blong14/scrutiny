import logging
from typing import List, Optional
from urllib import parse

import requests


from scrutiny.env import get_mercure_token, get_mercure_url


logger = logging.getLogger(__name__)


def send(msg: List[str]) -> Optional[requests.models.Response]:
    token = get_mercure_token()
    if not token:
        raise EnvironmentError("missing jwt publish token")
    resp: Optional[requests.models.Response] = None
    try:
        resp = requests.post(
            get_mercure_url(),
            data=parse.urlencode(
                {"target": "animate-graph", "topic": ["animate-graph"], "data": msg},
                True,
            ),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            verify=False,
        )
    except Exception as e:
        logger.error("unknown error %s dispatching event", e)
    if resp and resp.status_code != 200:
        logger.error("error dispatching event %s", resp)
    return resp
