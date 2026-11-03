import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from .realtime_service import PartyRealtimeService


logger = logging.getLogger("api.live_map.party")


async def cleanup_loop():
    after_id = None
    while True:
        await asyncio.sleep(15)
        try:
            def cleanup():
                return PartyRealtimeService().cleanup_batch(after_id)

            after_id = await run_in_threadpool(cleanup)
        except (RedisError, SQLAlchemyError, HTTPException) as exc:
            # Redis outages must not be interpreted as everyone disconnecting.
            logger.warning("Party cleanup postponed (%s)", type(exc).__name__)


@asynccontextmanager
async def party_lifespan(app):
    task = None
    if os.getenv("PARTY_CLEANUP_ENABLED", "true").lower() != "false":
        task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
