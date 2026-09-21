import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from .realtime_service import PartyRealtimeServiceV3


logger_v3 = logging.getLogger("api.live_map.party_v3")


async def cleanup_loop_v3():
    after_id = None
    while True:
        await asyncio.sleep(15)
        try:
            def cleanup_v3():
                return PartyRealtimeServiceV3().cleanup_batch_v3(after_id)

            after_id = await run_in_threadpool(cleanup_v3)
        except (RedisError, SQLAlchemyError, HTTPException) as exc:
            # Redis outages must not be interpreted as everyone disconnecting.
            logger_v3.warning("Party cleanup postponed (%s)", type(exc).__name__)


@asynccontextmanager
async def party_lifespan_v3(app):
    task = None
    if os.getenv("PARTY_CLEANUP_ENABLED", "true").lower() != "false":
        task = asyncio.create_task(cleanup_loop_v3())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
