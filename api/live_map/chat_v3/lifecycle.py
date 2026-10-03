import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from database import V3Database
from .service import ChatServiceV3


async def chat_cleanup_loop_v3():
    ticks = 0
    after_id = None
    while True:
        await asyncio.sleep(2)
        try:
            def cleanup_v3():
                with V3Database.SessionLocal.begin() as session:
                    service = ChatServiceV3(session)
                    next_id = service.reconcile_batch_v3(after_id)
                    if ticks % 30 == 0:
                        service.cleanup_v3()
                    return next_id
            after_id = await run_in_threadpool(cleanup_v3)
            ticks += 1
        except SQLAlchemyError as exc:
            logging.getLogger('api.live_map.chat_v3').warning('Chat cleanup postponed (%s)', type(exc).__name__)


@asynccontextmanager
async def chat_lifespan_v3(app):
    task = asyncio.create_task(chat_cleanup_loop_v3())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
