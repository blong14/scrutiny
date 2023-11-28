import asyncio
import json
import logging

import aio_pika
import aio_pika.abc
from django.core.management.base import BaseCommand

from scrutiny.env import get_rmq_dsn  # noqa
from .news_summary import get_summary


async def main(loop: asyncio.AbstractEventLoop, dsn: str) -> None:
    connection = await aio_pika.connect_robust(dsn, loop=loop)
    async with connection:
        queue_name = "news-summary"
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            queue_name,
            auto_delete=True
        )
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                msg = json.loads(message.body.decode())
                logging.info("consuming message %s", msg)
                await message.ack()
                if msg.get("action") == "start":
                    try:
                        await get_summary()
                    except Exception:
                        logging.exception("unable to process message %s", msg)
                        continue


class Command(BaseCommand):
    help = "Start News Summary"

    def handle(self, *args, **options) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop, get_rmq_dsn()))
        loop.close()
