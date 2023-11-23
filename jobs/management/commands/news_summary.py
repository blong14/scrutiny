import asyncio
import logging
from typing import Any, List
from urllib import parse

import aiohttp
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass
from pydantic import BaseModel

from scrutiny.env import (
    get_mercure_url,
    get_mercure_pub_token,
)

from jobs.models import Job  # noqa
from news.models import FeedRegistry, parse_feed  # noqa


@dataclass
class HttpRequest:
    session: Any
    base_url: str = "https://getpocket.com"
    read_timeout: float = 10.0
    header = {"Content-Type": "application/json"}


@dataclass
class Response:
    data: List
    success: bool = False


class Token(BaseModel):
    done: bool
    model: str
    response: str


READ_TIMEOUT = 300.0
ERROR_RESPONSE = Response(data=[], success=False)


async def _mercure_request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        async with req.session.request(method, url, ssl=False, **kwargs) as resp:
            await resp.text()
    except asyncio.TimeoutError:
        logging.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logging.error(e)
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        return Response(success=True, data=[])


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    data = []
    try:
        kwargs |= dict(headers=req.header)
        async with req.session.request(method, url, ssl=False, **kwargs) as resp:
            async for chunk in resp.content.iter_chunks():
                token = Token.model_validate_json(chunk[0])
                if token.done:
                    break
                data.append(token.response)
    except asyncio.TimeoutError:
        logging.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logging.error(e)
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        return Response(success=True, data=data)


async def get_ollama(req):
    context = {}
    feed = FeedRegistry.get("hackernews")
    context = parse_feed(context, feed)
    titles = "; ".join([itm.get("title") for itm in context.get("items", [])])
    prompt = f"""Given these titles, {titles}, create a summary paragraph.
    Make the summary sound like a technical writer wrote the summary and do not
    include the titles in the response. Do not include lists or bullet points and
    only use full sentences. Your response should start with `Today's News: `
    """
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        "http://ollama.cluster/api/generate",
        json={
            "model": "orca-mini",
            "prompt": prompt,
        },
    )
    if not resp.success:
        return []
    return resp.data


async def mercure(req, data):
    summary = ""
    for token in data:
        summary = f"{summary} {token}"
        msg = render_to_string("jobs/news_summary.html", {"summary": summary})
        await _mercure_request(
            req,
            aiohttp.hdrs.METH_POST,
            get_mercure_url(),
            data=parse.urlencode(
                {"target": "news-summary", "topic": ["jobs"], "data": msg},
                True,
            ),
        )


async def create_job_event(name: str, data: dict) -> Job:
    job = Job(name=name, data=data)
    await job.asave()
    await job.arefresh_from_db()
    return job


async def main():
    event = await create_job_event(
        name="news_summary",
        data={"version": "1"},
    )

    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        data = await get_ollama(HttpRequest(session=session))

    pub_token = get_mercure_pub_token()
    if not pub_token:
        raise EnvironmentError("missing jwt publish token")

    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
        headers={
            "Authorization": f"Bearer {pub_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    ) as session:
        await mercure(HttpRequest(session=session), data),

    event.status = "success"
    await event.asave()


class Command(BaseCommand):
    help = "Start News Summary"

    def handle(self, *args, **options) -> None:
        asyncio.run(main())
