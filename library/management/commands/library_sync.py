import asyncio
import logging
from typing import Any, Union, Dict, List

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


async def fetch_data(req, usr) -> Dict[int, Dict[str, Union[Article | List[Tag]]]]:
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
        return {}
    return {
        item.get("item_id"): {
            "article": Article(
                id=item.get("item_id"),
                authors=item.get("authors", {}),
                excerpt=item.get("excerpt"),
                user=usr.user,
                listen_duration_estimate=item.get("listen_duration_estimate"),
                resolved_title=item.get("resolved_title"),
            ),
            "tags": [
                Tag(
                    pk=tag.get("item_id"),
                    value=tag.get("tag"),
                    user=usr.user,
                )
                for tag in item.get("tags", {}).values()
                if tag.get("item_id")
            ],
        }
        for _, item in resp.data.get("list", {}).items()
    }


async def articles(req: HttpRequest, usr: UserSocialAuth) -> List[Article]:
    articles_and_tags = await fetch_data(req, usr)
    all_articles, all_tags, tag_set = [], [], set()
    for article_id, data in articles_and_tags.items():
        all_articles.append(data.get("article"))
        for tag in data.get("tags"):
            if tag.value not in tag_set:
                tag_set.add(tag.value)
                all_tags.append(tag)

    await asyncio.gather(
        asyncio.ensure_future(
            sync_to_async(Article.objects.bulk_create, thread_sensitive=True)(
                all_articles,
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
        ),
        asyncio.ensure_future(
            sync_to_async(Tag.objects.bulk_create, thread_sensitive=True)(
                all_tags,
                ignore_conflicts=True,
                unique_fields=["value"],
            )
        ),
    )

    await asyncio.gather(
        *[
            asyncio.ensure_future(
                sync_to_async(d.get("article").tags.set, thread_sensitive=True)(
                    [
                        t
                        for tag in d.get("tags", [])
                        for t in all_tags
                        if t.value == tag.value
                    ]
                )
            )
            for _, d in articles_and_tags.items()
            if d.get("tags", [])
        ]
    )
    return all_articles


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
        self.stdout.write(self.style.SUCCESS("syncing library"))
        asyncio.run(main())
        self.stdout.write(self.style.SUCCESS("finished syncing library"))
