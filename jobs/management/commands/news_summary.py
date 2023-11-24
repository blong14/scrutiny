import asyncio
from asgiref.sync import sync_to_async
from collections.abc import AsyncIterable
from urllib import parse

import aiohttp
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand
from pydantic import BaseModel, ConfigDict

from jobs.models import Job  # noqa
from news.models import FeedRegistry, parse_feed  # noqa
from scrutiny.env import (  # noqa
    get_mercure_url,
    get_mercure_pub_token,
    get_ollama_url,
)


class HttpRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session: aiohttp.ClientSession


class Token(BaseModel):
    done: bool
    model: str
    response: str


READ_TIMEOUT = 300.0
SEND_TIMEOUT = 10.0


async def _read_tokens(req: HttpRequest, **kwargs) -> AsyncIterable[Token, None]:
    async with req.session.request(
        aiohttp.hdrs.METH_POST,
        f"{get_ollama_url()}/api/generate",
        ssl=False,
        **kwargs,
    ) as resp:
        async for chunk, valid in resp.content.iter_chunks():
            if not valid:
                return
            yield Token.model_validate_json(chunk)


async def read_tokens(req: HttpRequest) -> AsyncIterable[str, None]:
    feed = FeedRegistry.get("hackernews")
    context = {}
    context = await sync_to_async(parse_feed)(context, feed)
    titles = "; ".join([itm.get("title") for itm in context.get("items", [])])
    prompt = f"""Given these titles, {titles}, create a summary paragraph.
    Make the summary sound like a technical writer wrote the summary and do not
    include the titles in the response. Do not include lists or bullet points and
    only use full sentences. Your response should start with `Today's News: `
    """
    data = {"model": "orca-mini", "prompt": prompt}
    async for token in _read_tokens(req, json=data):
        yield token.response
        if token.done:
            return


async def _send(req: HttpRequest, **kwargs) -> None:
    await req.session.request(
        aiohttp.hdrs.METH_POST,
        get_mercure_url(),
        ssl=False,
        **kwargs
    )


async def send(req: HttpRequest, summary: str) -> None:
    msg = await sync_to_async(render_to_string)(
        "jobs/news_summary.html", {"summary": summary}
    )
    await _send(req, data=parse.urlencode(
        {"target": "news-summary", "topic": ["jobs"], "data": msg},
        True,
    ))


async def create_job_event(name: str, data: dict) -> Job:
    job = Job(name=name, data=data)
    await job.asave()
    await job.arefresh_from_db()
    return job


async def main() -> None:
    pub_token = get_mercure_pub_token()
    if not pub_token:
        raise EnvironmentError("missing jwt publish token")

    event = await create_job_event(
        name="news_summary",
        data={"version": "1"},
    )

    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        mercure_session = aiohttp.ClientSession(
            trust_env=False,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=SEND_TIMEOUT),
            headers={
                "Authorization": f"Bearer {pub_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        await send(HttpRequest(session=mercure_session), "Chat client started...")
        summary = ""
        async for token in read_tokens(HttpRequest(session=session)):
            summary = f"{summary}{token}"
            await send(HttpRequest(session=mercure_session), summary)
        await mercure_session.close()

    event.status = "success"
    await event.asave()


class Command(BaseCommand):
    help = "Start News Summary"

    def handle(self, *args, **options) -> None:
        asyncio.run(main())
