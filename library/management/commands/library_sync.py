import asyncio
import logging
import time
from typing import Any, List

import aiohttp
from asgiref.sync import sync_to_async
from asyncio.tasks import Task
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from library.models import Article, Tag
from scrutiny.env import get_pocket_consumer_key


@dataclass
class HttpRequest:
    session: Any
    base_url: str = "https://getpocket.com"
    read_timeout: float = 10.0
    header = {"Content-Type": "application/json"}


@dataclass
class Response:
    data: dict
    success: bool = False


class ArticleModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    article: Article
    tags: List[Tag]


READ_TIMEOUT = 10.0
ERROR_RESPONSE = Response(data=dict(), success=False)


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        kwargs |= dict(headers=req.header)
        async with req.session.request(method, url, ssl=True, **kwargs) as resp:
            data = await resp.json()
    except asyncio.TimeoutError:
        logging.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logging.error(e)
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        return Response(success=True, data=data)


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
            tags=[
                Tag(
                    pk=tag.get("item_id"),
                    value=tag.get("tag"),
                    user=usr.user,
                )
                for tag in item.get("tags", {}).values()
                if tag.get("item_id")
            ],
        )
        for _, item in resp.data.get("list", {}).items()
    ]


def get_articles() -> Task:
    return asyncio.ensure_future(
        sync_to_async(Article.objects.all().values_list)("id", flat=True)
    )


def create_articles(data: List[Article]) -> Task:
    return asyncio.ensure_future(
        sync_to_async(Article.objects.bulk_create)(
            data,
            ignore_conflicts=True,
            update_fields=[
                "authors",
                "excerpt",
                "slug",
                "resolved_title",
                "listen_duration_estimate",
            ],
            unique_fields=["id"],
        )
    )


def create_tags(data: List[Tag]) -> Task:
    return asyncio.ensure_future(
        sync_to_async(Tag.objects.bulk_create)(
            data,
            ignore_conflicts=True,
            unique_fields=["id"],
        )
    )


async def create_article_tags(data: List[ArticleModel]) -> list:
    results = [
        result
        for result in await asyncio.gather(
            *[
                asyncio.ensure_future(sync_to_async(item.article.tags.set)(item.tags))
                for item in data
                if item.tags
            ]
        )
    ]
    return results


async def main():
    logging.info("starting requests...")
    usr = await sync_to_async(
        User.objects.filter(
            username="14benj@gmail.com",
            is_superuser=False,
        )
        .first()
        .social_auth.first,
        thread_sensitive=True,
    )()
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        items, existing_articles = await asyncio.gather(
            get_pocket_data(HttpRequest(session=session), usr),
            get_articles(),
        )
    new_articles = [
        item.article for item in items if item.article.id not in existing_articles
    ]
    new_tags = [
        tag
        for item in items
        for tag in item.tags
        if item.article.id not in existing_articles
    ]
    new_article_tags = [
        ArticleModel(article=item.article, tags=item.tags)
        for item in items
        if item.article.id not in existing_articles
    ]
    _ = [
        result
        for result in await asyncio.gather(
            create_tags(new_tags),
            create_articles(new_articles),
        )
    ]
    await create_article_tags(new_article_tags)
    logging.info("finished creating %d", len(items))


class Command(BaseCommand):
    help = "Start Pocket API Sync"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("syncing library"))
        trace_start = time.perf_counter()
        asyncio.run(main())
        duration = time.perf_counter() - trace_start
        self.stdout.write(
            self.style.SUCCESS(f"finished syncing library in {duration:0.3f}s")
        )
