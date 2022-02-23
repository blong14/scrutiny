import asyncio
import logging
from typing import Any, List, Tuple

import aiohttp
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass

from notes.models import Note, Project


logger = logging.getLogger(__name__)


@dataclass
class HttpRequest:
    session: Any
    token: str = ""
    base_url: str = "https://api.graftapp.co"
    read_timeout: float = 10.0
    user: str = "14benj@gmail.com"
    password: str = "Xg00rgO2bRpe"

    @property
    def header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


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


async def get_token(session: aiohttp.ClientSession) -> Response:
    req = HttpRequest(session=session)
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        f"{req.base_url}/v1/auth/login/",
        json=dict(email=req.user, password=req.password),
    )
    return resp.data.get("access_token")


async def create_project_with_notes(
    req: HttpRequest, **kwargs
) -> Tuple[Project, List[Note]]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_GET,
        f"{req.base_url}/v1/projects/{kwargs.get('slug')}/notes/",
    )
    prj = Project(**kwargs)
    await sync_to_async(prj.save, thread_sensitive=True)()
    notes = [
        Note(
            project_id=prj.id,
            slug=n["id"],
            title=n["title"],
            body=n["body"],
        )
        for n in resp.data.get("items", [])
    ]
    return prj, notes


async def projects(req: HttpRequest, usr: User) -> List[Tuple[Project, List[Note]]]:
    resp = await _request(req, aiohttp.hdrs.METH_GET, f"{req.base_url}/v1/projects/")
    if not resp.success:
        return []
    logger.info(resp.data.get("items"))
    future_projects = [
        asyncio.ensure_future(
            create_project_with_notes(
                req,
                user=usr,
                slug=data.get("id"),
                title=data.get("title"),
            ),
        )
        for data in resp.data.get("items", [])
    ]
    return [
        (project, notes) for project, notes in await asyncio.gather(*future_projects)
    ]


async def main():
    await sync_to_async(Project.objects.all().delete, thread_sensitive=True)()
    await sync_to_async(Note.objects.all().delete, thread_sensitive=True)()
    usr = await sync_to_async(
        User.objects.filter(username="14benj@gmail.com", is_superuser=False).first,
        thread_sensitive=True,
    )()
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        logger.info("starting requests...")
        token = await get_token(session)
        logger.info("requesting data...")
        tasks = [
            asyncio.ensure_future(fn(HttpRequest(session=session, token=token), usr))
            for fn in (projects,)
        ]
        for data in await asyncio.gather(*tasks):
            for _, notes in data:
                await sync_to_async(Note.objects.bulk_create, thread_sensitive=True)(
                    notes
                )
        logger.info("finished")


class Command(BaseCommand):
    help = "Start Sync Graft API"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("syncing graft api"))
        asyncio.run(main())
        self.stdout.write(self.style.SUCCESS("finished syncing graft api"))
