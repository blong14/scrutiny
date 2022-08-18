import asyncio
import logging
from typing import Any, Awaitable, List

import aiohttp
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass
from social_django.models import UserSocialAuth

from library.models import Article, Tag
from scrutiny.env import get_pocket_consumer_key


logger = logging.getLogger(__name__)


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


READ_TIMEOUT = 10.0
ERROR_RESPONSE = Response(data=dict(), success=False)


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        kwargs |= dict(headers=req.header)
        async with req.session.request(method, url, ssl=True, **kwargs) as resp:
            data = await resp.json()
    except asyncio.TimeoutError:
        logger.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logger.error(e)
        logger.warning("sleeping...")
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        return Response(success=True, data=data)


async def articles(req: HttpRequest, usr: UserSocialAuth) -> List[Article]:
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
    new_articles: List[Article] = []
    future_articles = []
    for _, item in resp.data.get("list", {}).items():
        tags = item.get("tags")
        article = Article(
            id=item.get("item_id"),
            authors=item.get("authors", {}),
            excerpt=item.get("excerpt"),
            user=usr.user,
            listen_duration_estimate=item.get("listen_duration_estimate"),
            resolved_title=item.get("resolved_title"),
        )

        def save(art, tgs):
            art.save()
            return art, tgs

        future_articles.append(
            asyncio.ensure_future(
                sync_to_async(save, thread_sensitive=True)(article, tags),
            ),
        )
    all_tags = set()
    for article, tags in await asyncio.gather(*future_articles):
        if not tags:
            continue
        future_tags: List[Awaitable] = []
        for tag in tags:
            if tag in all_tags:
                article.tags.add(tag, bulk=True)
                continue
            future_tags.append(
                asyncio.ensure_future(
                    sync_to_async(
                        Tag.objects.update_or_create,
                        thread_sensitive=True,
                    )(defaults={"value": tag, "user": usr.user}, value=tag),
                )
            )
        tags_for_article: List[Tag] = []
        for tag, _ in await asyncio.gather(*future_tags):
            all_tags.add(tag)
            tags_for_article.append(tag)
        article.tags.set(tags_for_article)
        new_articles.append(article)
    return new_articles


async def main():
    await sync_to_async(Article.objects.all().delete, thread_sensitive=True)()
    await sync_to_async(Tag.objects.all().delete, thread_sensitive=True)()
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        logger.info("starting requests...")
        usr = await sync_to_async(
            User.objects.filter(username="14benj@gmail.com", is_superuser=False)
            .first()
            .social_auth.first,
            thread_sensitive=True,
        )()
        items = await articles(HttpRequest(session=session), usr)
        logger.info("finished creating %d", len(items))


class Command(BaseCommand):
    help = "Start Pocket API Sync"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("syncing graft api"))
        asyncio.run(main())
        self.stdout.write(self.style.SUCCESS("finished syncing graft api"))
