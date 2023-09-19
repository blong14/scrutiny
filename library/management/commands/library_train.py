import asyncio
import collections
import logging
import random
import time
from asyncio import Future
from asyncio.tasks import Task
from typing import Any, List

import aiohttp
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from social_django.models import UserSocialAuth

from library.models import Article, JobEvent, LM, Tag
from scrutiny.env import get_pocket_consumer_key


@dataclass
class HttpRequest:
    session: Any
    base_url: str = "https://getpocket.com"
    read_timeout: float = 10.0
    header = {"Content-Type": "application/json"}


@dataclass
class Response:
    data: str
    success: bool = False


class ArticleModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    article: Article


READ_TIMEOUT = 10.0
ERROR_RESPONSE = Response(data="error", success=False)


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        kwargs |= dict(headers=req.header)
        async with req.session.request(method, url, ssl=True, **kwargs) as resp:
            data = await resp.text()
    except asyncio.TimeoutError:
        logging.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logging.error(e)
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        text = BeautifulSoup(data, features="html.parser")
        body = text.find("body")
        if not body:
            print(text)
            return Response(success=True, data="")
        processed_text = body.findAll(text=True, recursive=True)
        return Response(
            success=True,
            data=" ".join([a.strip() for a in processed_text if a != "\n"]),
        )


class LanguageModel(collections.defaultdict):
    """A mapping from `order` history characters to possible next characters and their
    frequency, e.g. {'spea': Counter({'k': 9, 'r': 1})} lets us generate 'speak' or 'spear'.
    """

    def __init__(self, order):
        super().__init__()
        self.order = order
        self.default_factory = collections.Counter


PAD = "`"  # Character to pad the beginning of a text


def train_char_lm(text: str, order=4) -> LanguageModel:
    """Train an character-level language model of given order on all the text in `fname`."""
    lm = LanguageModel(order)
    data = (order * PAD) + text
    for i in range(order, len(data)):
        history, char = data[i - order : i], data[i]
        lm[history][char] += 1
    for counter in lm.values():
        counter.total = sum(
            counter.values()
        )  # Cache total counts (for sample_character)
    return lm


def P(c, h, lm) -> float:
    """The probability P(c | h) of next character c given history h, according to the language model."""
    return lm[h][c] / lm[h].total


def sample_character(counter) -> str:
    """Randomly sample the nth character from the counter."""
    n = random.randint(1, counter.total)
    cumulative = 0
    for c in counter:
        cumulative += counter[c]
        if cumulative >= n:
            return c


def generate_text(lm: LanguageModel, length=1000) -> str:
    """Sample a random `length`-long passage from `lm`."""
    history = lm.order * PAD
    text = []
    for _ in range(length):
        c = sample_character(lm[history])
        history = history[1:] + c
        text.append(c)
    return "".join(text)


async def read_articles(req) -> Future:
    articles = await asyncio.ensure_future(sync_to_async(Article.objects.all)())
    return asyncio.gather(
        *[_request(req, aiohttp.hdrs.METH_GET, a.resolved_url) for a in articles]
    )


async def get_pocket_data(req, usr) -> List[ArticleModel]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        f"{req.base_url}/v3/get",
        json={
            "consumer_key": get_pocket_consumer_key(),
            "access_token": usr.extra_data.get("access_token", ""),
            "contentType": "article",
            "detailType": "complete",
            "offset": 0,  # zero based
        },
    )
    if not resp.success:
        return []
    return [
        ArticleModel(
            article=Article(
                id=int(item.get("item_id")),
                authors=item.get("authors", {}),
                excerpt=item.get("excerpt"),
                user=usr.user,
                listen_duration_estimate=item.get("listen_duration_estimate"),
                resolved_title=item.get("resolved_title"),
            ),
        )
        for _, item in resp.data.get("list", {}).items()
    ]


def create_job_event(data: dict) -> Task[int]:
    return asyncio.ensure_future(
        sync_to_async(JobEvent(data=data).save, thread_sensitive=False)()
    )


def read_user(email: str) -> Task[UserSocialAuth]:
    return asyncio.ensure_future(
        sync_to_async(
            User.objects.filter(
                username=email,
                is_superuser=False,
            )
            .first()
            .social_auth.first,
            thread_sensitive=False,
        )()
    )


async def main():
    # create_job_event({"name": "start", "version": "1"}),

    # async with aiohttp.ClientSession(
    #     trust_env=False,
    #     raise_for_status=True,
    #     timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    # ) as session:
    #     articles = await read_articles(HttpRequest(session=session))
    #     all_text = [article.data for article in await articles]
    # await asyncio.ensure_future(
    #     sync_to_async(LM(excerpt=all_text).save, thread_sensitive=False)()
    # )

    all_text = await asyncio.ensure_future(
        sync_to_async(LM.objects.all, thread_sensitive=False)()
    )
    lm = train_char_lm(list(all_text)[-1].excerpt, order=16)
    print("\n\n******************\n\n")
    print(generate_text(lm, length=10000))


class Command(BaseCommand):
    help = "Language Model Training"

    def handle(self, *args, **options) -> None:
        trace_start = time.perf_counter()
        asyncio.run(main())
        duration = time.perf_counter() - trace_start
        self.stdout.write(
            self.style.SUCCESS(f"finished training library in {duration:0.3f}s")
        )
