import asyncio
import logging
import random
from typing import Any, Callable, List, Optional, Tuple, Type, TypeVar, Union, overload

import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand
from pydantic.dataclasses import dataclass as pyd_dataclass
from pydantic.fields import Field, FieldInfo

from news.models import Event


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
    base_url: str = "http://scrutiny-varnish.default"
    mercure_url: str = "http://scrutiny-caddy.default"
    read_timeout: float = 10.0
    token = settings.JWT_PUBLISH_TOKEN


@dataclass(frozen=True)
class Response:
    data: dict
    success: bool = False


READ_TIMEOUT = 10.0
ERROR_RESPONSE = Response(data=dict(), success=False)


async def _request(req: HttpRequest, method: str, url: str, **kwargs) -> Response:
    try:
        async with req.session.request(method, url, ssl=False, **kwargs) as resp:
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


async def events(req: HttpRequest) -> List[Event]:
    resp = await _request(
        req,
        aiohttp.hdrs.METH_GET,
        f"{req.base_url}/api/news/events/",
    )
    return [
        Event(
            event_id=data.get("event_id"),
            event_data=data.get("event_data"),
        )
        for data in resp.data
    ]


async def dispatch(req: HttpRequest, event: Event):
    resp = await _request(
        req,
        aiohttp.hdrs.METH_POST,
        f"{req.mercure_url}/.well-known/mercure?",
        data=parse.urlencode(event.event_data, True),
        headers={
            "Authorization": f"Bearer {req.token}",
            "Content-Type": "application/x-www-form-urlencede",
        },
    )
    return [
        Event(
            event_id=data.get("event_id"),
            event_data=data.get("event_data"),
        )
        for data in resp.data
    ]


async def main():
    while True:
        time.sleep(60)
        async with aiohttp.ClientSession(
            trust_env=False,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=READ_TIMEOUT),
        ) as session:
            logger.info("starting requests...")
            for event in await events(HttpRequest()):
                notify(event)
            logger.info("finished")


class Command(BaseCommand):
    help = "Start Consuming News items created events"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("consuming..."))
        asyncio.run(main())
        self.stdout.write(self.style.SUCCESS("finished consuming."))
