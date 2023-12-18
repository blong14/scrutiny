import asyncio
import json
import logging

import aio_pika
import aio_pika.abc
from django.core.management.base import BaseCommand

from scrutiny.env import get_rmq_dsn  # noqa
from .library_sync import main

logger = logging.getLogger(__name__)


async def consume(loop: asyncio.AbstractEventLoop, dsn: str) -> None:
    logger.debug("connecting to rmq...")
    connection = await aio_pika.connect_robust(dsn, loop=loop)
    async with connection:
        queue_name = "library-sync"
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            queue_name, auto_delete=True
        )
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await message.ack()
                msg = json.loads(message.body.decode())
                logger.info("message %s", msg)
                try:
                    await main()
                except Exception:
                    logging.exception("unable to process message %s", msg)
                    continue


class Command(BaseCommand):
    help = "Start Library Sync"

    def handle(self, *args, **options) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(consume(loop, get_rmq_dsn()))
        loop.close()
