import logging
import json
from typing import Optional

import requests
from pydantic.dataclasses import dataclass


@dataclass
class HttpRequest:
    base_url: str = "https://getpocket.com"
    read_timeout: float = 10.0
    header = {"Content-Type": "application/json", "X-Accept": "application/json"}
    data: Optional[dict] = None


@dataclass
class Response:
    data: dict
    success: bool = False


class PocketClient:
    READ_TIMEOUT = 10.0
    ERROR_RESPONSE = Response(data=dict(), success=False)

    def add(self, req: HttpRequest) -> Response:
        try:
            resp = requests.post(
                f"{req.base_url}/v3/add",
                json=req.data,
                headers=req.header,
                timeout=self.READ_TIMEOUT,
            )
            resp.raise_for_status()
        except Exception as e:
            logging.error(e)
            return self.ERROR_RESPONSE
        else:
            return Response(data=resp.json(), success=True)
