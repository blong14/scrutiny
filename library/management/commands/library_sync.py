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

from library.models import Article, JobEvent, Tag
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
                    value=tag.get("tag"),
                    article_id=tag.get("item_id"),
                    user=usr.user,
                )
                for tag in item.get("tags", {}).values()
                if tag.get("item_id")
            ],
        )
        for _, item in resp.data.get("list", {}).items()
    ]


def create_job_event(data: dict) -> Task:
    return asyncio.ensure_future(
        sync_to_async(JobEvent(data=data).save, thread_sensitive=False)()
    )


def get_articles() -> Task:
    return asyncio.ensure_future(
        sync_to_async(Article.objects.all().values_list)("id", flat=True)
    )


def get_user(email: str) -> Task:
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


def create_articles(data: List[Article]) -> Task:
    return asyncio.ensure_future(
        sync_to_async(Article.objects.bulk_create, thread_sensitive=False)(
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


def delete_articles(data: List[Article]) -> Task:
    query = Article.objects.filter(id__in=data)
    return asyncio.ensure_future(
        sync_to_async(query.delete, thread_sensitive=False)()
    )


def create_tags(data: List[Tag]) -> Task:
    return asyncio.ensure_future(
        sync_to_async(Tag.objects.bulk_create, thread_sensitive=False)(
            data,
            update_fields=["value"],
            unique_fields=["id"],
        )
    )


async def main():
    usr, event = await asyncio.gather(
        get_user("14benj@gmail.com"),
        create_job_event({"name": "start", "version": "1"}),
    )
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        items, existing_articles = await asyncio.gather(
            get_pocket_data(HttpRequest(session=session), usr),
            get_articles(),
        )
        raw_source_ids = [item.article.id for item in items]
    new_articles = [
        item.article for item in items if item.article.id not in existing_articles
    ]
    to_delete = [
        article for article in existing_articles if article not in raw_source_ids
    ]
    await asyncio.gather(create_articles(new_articles), delete_articles(to_delete))
    new_tags = [
        tag
        for item in items
        for tag in item.tags
        if item.article.id not in existing_articles
    ]
    await create_tags(new_tags)
    await create_job_event(
        {
            "name": "end",
            "version": "1",
            "results": {
                "existing_articles": len(existing_articles),
                "new_articles": len(new_articles),
                "new_tags": len(new_tags),
                "raw_items": len(items),
            },
        }
    )


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
