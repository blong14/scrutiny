import asyncio
import logging
from itertools import chain
from typing import Any, Dict, List, Optional

import aiohttp
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass

from scrutiny.env import get_graft_api_key
from notes.models import Note, Project


@dataclass
class Position:
    project_id: int
    note_id: str
    x: float
    y: float


@dataclass
class HttpRequest:
    session: Any
    token: str = ""
    base_url: str = "https://api.graftapp.co"
    read_timeout: float = 10.0
    user: str = "14benj@gmail.com"
    password: str = ""

    @property
    def header(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


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
        logging.error(f"asyncio.TimeOutError {req.read_timeout}")
        return ERROR_RESPONSE
    except aiohttp.ClientResponseError as e:
        logging.error(e)
        logging.warning("sleeping...")
        await asyncio.sleep(3)
        return ERROR_RESPONSE
    else:
        return Response(success=True, data=data)


async def get_user() -> User:
    return await sync_to_async(
        User.objects.filter(username="14benj@gmail.com", is_superuser=False).first,
        thread_sensitive=True,
    )()


async def get_token(session: aiohttp.ClientSession) -> Response:
    req = HttpRequest(session=session)
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        f"{req.base_url}/v1/auth/login/",
        json=dict(email=req.user, password=get_graft_api_key()),
    )
    return resp.data.get("access_token")


async def get_positions(
    req: HttpRequest, project: Project, **kwargs
) -> Dict[str, Position]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_GET,
        f"{req.base_url}/v1/projects/{kwargs.get('slug')}/positions/",
    )
    positions = {
        p["note_id"]: Position(
            project_id=project.id,
            note_id=p["note_id"],
            x=p["fx"],
            y=p["fy"],
        )
        for p in resp.data.get("items", [])
    }
    return positions


async def get_notes(req: HttpRequest, project: Project, **kwargs) -> List[Note]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_GET,
        f"{req.base_url}/v1/projects/{kwargs.get('slug')}/notes/",
    )
    notes = [
        Note(
            project_id=project.id,
            slug=n["id"],
            title=n["title"],
            body=n["body"],
            neighbors=n["neighbors"],
        )
        for n in resp.data.get("items", [])
    ]
    return notes


async def create_project_with_notes_and_positions(
    req: HttpRequest, **kwargs
) -> List[Note]:
    existing_projects = kwargs.pop("existing_projects", [])
    slug = kwargs.get("slug", "")
    prj: Optional[Project] = None
    for project in existing_projects:
        if project.slug == slug:
            prj = project
            break
    if not prj:
        prj = Project(**kwargs)
        await sync_to_async(prj.save, thread_sensitive=True)()
    notes, positions = await asyncio.gather(
        asyncio.ensure_future(get_notes(req, project=prj, **kwargs)),
        asyncio.ensure_future(get_positions(req, project=prj, **kwargs)),
    )
    for n in notes:
        position = positions.get(n.slug)
        if position:
            n.position = {"x": position.x, "y": position.y}
    return notes


async def projects(
    req: HttpRequest, usr: User, existing_projects: List[Project]
) -> List[List[Note]]:
    resp = await _request(req, aiohttp.hdrs.METH_GET, f"{req.base_url}/v1/projects/")
    if not resp.success:
        return []
    future_projects = [
        asyncio.ensure_future(
            create_project_with_notes_and_positions(
                req,
                user=usr,
                slug=data.get("id"),
                title=data.get("title"),
                existing_projects=existing_projects,
            ),
        )
        for data in resp.data.get("items", [])
    ]
    return [notes for notes in await asyncio.gather(*future_projects)]


async def sync():
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        usr, token = await asyncio.gather(
            asyncio.ensure_future(get_user()),
            asyncio.ensure_future(get_token(session)),
        )
        existing_projects = await sync_to_async(
            Project.objects.filter(user=usr).prefetch_related("notes").all,
            thread_sensitive=False,
        )()
        existing_notes = [
            note.slug for project in existing_projects for note in project.notes.all()
        ]
        await sync_to_async(Note.objects.bulk_create, thread_sensitive=True)(
            [
                note
                for note in list(
                    chain(
                        *await projects(
                            HttpRequest(session=session, token=token),
                            usr,
                            existing_projects,
                        )
                    )
                )
                if note.slug not in existing_notes
            ]
        )


class Command(BaseCommand):
    help = "Start Sync Graft API"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("syncing graft api"))
        asyncio.run(sync())
        self.stdout.write(self.style.SUCCESS("finished syncing graft api"))
