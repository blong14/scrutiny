import asyncio
import logging

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
    get_mercure_svc_url,
    get_mercure_pub_token,
    get_ollama_svc_url,
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
        f"{get_ollama_svc_url()}/api/generate",
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
    prompt = f"""You are advanced chatbot Editor-in-chief Assistant. You can help users
    with editorial tasks, including proofreading and reviewing articles. Your ultimate goal
    is to help users create high-quality content. The user will give you a text to summarize,
    you will do so without making any comments on the subject, don't leave important details out.
    Provide a summary paragraph for these article titles, {titles}.
    """
    data = {"model": "orca-mini", "prompt": prompt}
    async for token in _read_tokens(req, json=data):
        yield token.response
        if token.done:
            return


async def _send(req: HttpRequest, **kwargs) -> None:
    await req.session.request(
        aiohttp.hdrs.METH_POST, get_mercure_svc_url(), ssl=False, **kwargs
    )


async def send(req: HttpRequest, summary: str) -> None:
    msg = await sync_to_async(render_to_string)(
        "jobs/news_summary.html", {"summary": summary}
    )
    await _send(
        req,
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


async def get_summary() -> None:
    pub_token = get_mercure_pub_token()
    if not pub_token:
        raise EnvironmentError("missing jwt publish token")

    event = await create_job_event(
        name="news_summary",
        data={"version": "1"},
    )

    mercure_session = aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=SEND_TIMEOUT),
        headers={
            "Authorization": f"Bearer {pub_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        await send(HttpRequest(session=mercure_session), "Chat client started...")
    except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
        logging.exception(str(e))
        event.status = "error"
        await event.asave()
        return

    status = event.status

    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        summary = ""
        try:
            async for token in read_tokens(HttpRequest(session=session)):
                summary = f"{summary}{token}"
                await send(HttpRequest(session=mercure_session), summary)
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
            logging.exception(str(e))
            status = "error"
        else:
            status = "success"
        finally:
            await mercure_session.close()

    event.status = status
    await event.asave()


class Command(BaseCommand):
    help = "Start News Summary"

    def handle(self, *args, **options) -> None:
        asyncio.run(get_summary())
