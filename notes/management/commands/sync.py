import asyncio
import logging
import random
from typing import Any, Callable, List, Optional, Tuple, Type, TypeVar, Union, overload

import aiohttp
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass as pyd_dataclass
from pydantic.fields import Field, FieldInfo

from notes.models import Note, Project


logger = logging.getLogger(__name__)
_T = TypeVar("_T")


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, FieldInfo))
@overload
def dataclass(
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Callable[[Type[_T]], Type[_T]]:  # type: ignore
    ...


@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, FieldInfo))
@overload
def dataclass(
    _cls: Type[_T],
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Type[_T]:
    ...


@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, FieldInfo))
def dataclass(
    cls: Optional[Type[_T]] = None,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: Type[Any] = None,
) -> Union[Callable[[Type[Any]], Type[_T]], Type[_T]]:
    return pyd_dataclass(cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen, config=config)  # type: ignore


@dataclass(frozen=True, init=True)
class HttpRequest:
    session: Any
    token: str = ""
    base_url: str = "https://api.graftapp.co"
    read_timeout: float = 10.0
    user: str = "14benj@gmail.com"
    password: str = "g0zPZoS4NRhS"

    def header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


@dataclass(frozen=True)
class User:
    token: str
    email: str


@dataclass(frozen=True)
class Response:
    data: dict
    success: bool = False


READ_TIMEOUT = 10.0
ERROR_RESPONSE = Response(data=dict(), success=False)


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        kwargs |= dict(headers=req.header())
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
    return resp


async def user(req: HttpRequest) -> User:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        f"{req.base_url}/v1/auth/login/",
        json=dict(email=req.user, password=req.password),
    )
    return User(
        token=resp.data.get("access_token", ""),
        email=resp.data.get("user", dict()).get("email", ""),
    )


async def create_project_with_notes(
    req: HttpRequest, **kwargs
) -> Tuple[Project, List[Note]]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_GET,
        f"{req.base_url}/v1/projects/{kwargs.get('slug')}/notes/",
    )
    notes = [
        Note(
            id=random.randint(1, 1_000_000),
            slug=n["id"],
            title=n["title"],
            body=n["body"],
        )
        for n in resp.data.get("items", [])
    ]
    prj = Project(**kwargs)
    return prj, notes


async def projects(req: HttpRequest) -> List[Tuple[Project, List[Note]]]:
    resp = await _request(req, aiohttp.hdrs.METH_GET, f"{req.base_url}/v1/projects/")
    if not resp.success:
        return []
    future_projects = [
        asyncio.ensure_future(
            create_project_with_notes(
                # TODO: remove random int hack
                req,
                id=random.randint(1, 1_000_000),
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
    async with aiohttp.ClientSession(
        trust_env=False,
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
    ) as session:
        logger.info("starting requests...")
        usr = await user(HttpRequest(session=session, token=""))
        logger.info("requesting data...")
        tasks = [
            asyncio.ensure_future(fn(HttpRequest(session=session, token=usr.token)))
            for fn in (projects,)
        ]
        for data in await asyncio.gather(*tasks):
            for project, notes in data:
                await sync_to_async(project.save, thread_sensitive=True)()
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
