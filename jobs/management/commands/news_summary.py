import asyncio
import hashlib
import logging
from typing import TypedDict

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

logger = logging.getLogger(__name__)


class HttpRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session: aiohttp.ClientSession


class Token(BaseModel):
    done: bool
    model: str
    response: str


class JobArgs(TypedDict):
    version: str
    key: str


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


async def read_tokens(req: HttpRequest, titles: str) -> AsyncIterable[str, None]:
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


async def send(req: HttpRequest, summary: str) -> None:
    msg = await sync_to_async(render_to_string)(
        "jobs/news_summary.html", {"summary": summary}
    )
    await req.session.request(
        aiohttp.hdrs.METH_POST,
        get_mercure_svc_url(),
        ssl=False,
        data=parse.urlencode(
            {"target": "news-summary", "topic": ["news-summary"], "data": msg},
            True,
        ),
    )


async def send_job_update(req: HttpRequest, job: Job) -> None:
    msg = await sync_to_async(render_to_string)(
        "jobs/job_list_detail.html", {"job": job}
    )
    await req.session.request(
        aiohttp.hdrs.METH_POST,
        get_mercure_svc_url(),
        ssl=False,
        data=parse.urlencode(
            {"target": f"job-{job.id}", "topic": ["news-summary"], "data": msg},
            True,
        ),
    )


async def get_job_event(name: str, data: JobArgs) -> Job:
    job = await Job.objects.filter(
        name=name,
        data__key=data.get("key"),
        data__version=data.get("version"),
    ).afirst()
    return job


async def create_job_event(name: str, data: JobArgs) -> Job:
    job = Job(name=name, data=data)
    await job.asave()
    await job.arefresh_from_db()
    return job


async def get_summary() -> None:
    pub_token = get_mercure_pub_token()
    if not pub_token:
        raise EnvironmentError("missing jwt publish token")

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
        logger.debug("chat client started...")
        await send(HttpRequest(session=mercure_session), "Chat client started...")
    except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
        logger.exception("failed send to client")
        await mercure_session.close()
        return

    feed = FeedRegistry.get("hackernews")
    context = {}
    context = await sync_to_async(parse_feed)(context, feed)

    try:
        logger.debug("obtaining latest news...")
        await send(HttpRequest(session=mercure_session), "Obtaining latest news...")
    except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
        logger.exception("failed send to client")
        await mercure_session.close()
        return

    titles = "; ".join([itm.get("title") for itm in context.get("items", [])])
    h = hashlib.new("sha256")
    h.update(titles.encode())
    key = h.hexdigest()

    event = await get_job_event(
        name="news_summary",
        data={"key": key, "version": "1"},
    )

    if event is not None and event.status == "pending":
        logger.debug("skipping news summary")
        try:
            logger.debug("news summary pending...")
            await send(HttpRequest(session=mercure_session), "News summary pending...")
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
            logger.exception("failed send to client")
        finally:
            await mercure_session.close()
        return
    elif event is not None and event.status == "success":
        try:
            await send(HttpRequest(session=mercure_session), event.data["news-summary"])
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
            logger.exception("failed send to client")
        finally:
            await mercure_session.close()
        return

    logger.debug("starting news summary...")

    event = await create_job_event(
        name="news_summary",
        data={"key": key, "version": "1"},
    )

    try:
        await send_job_update(HttpRequest(session=mercure_session), event)
    except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
        logger.exception("failed send to client")
        await mercure_session.close()
        return

    status = event.status

    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        summary = ""
        try:
            logger.debug("reading tokens...")
            async for token in read_tokens(HttpRequest(session=session), titles):
                summary = f"{summary}{token}"
                await send(HttpRequest(session=mercure_session), summary)
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
            logger.exception("failed to send summary to client")
            status = "error"
        else:
            status = "success"

    logger.debug("saving event with status %s", status)
    event.status = status
    event.data["news-summary"] = summary
    await event.asave()

    try:
        await send_job_update(HttpRequest(session=mercure_session), event)
    except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
        logger.exception("failed send to client")
    finally:
        await mercure_session.close()


class Command(BaseCommand):
    help = "Start News Summary"

    def handle(self, *args, **options) -> None:
        asyncio.run(get_summary())
