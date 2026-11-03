import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from database import Database
from .service import ChatService


async def chat_cleanup_loop():
    ticks = 0
    after_id = None
    while True:
        await asyncio.sleep(2)
        try:
            def cleanup():
                with Database.SessionLocal.begin() as session:
                    service = ChatService(session)
                    service.expire_sessions()
                    next_id = service.reconcile_batch(after_id)
                    if ticks % 30 == 0:
                        service.cleanup()
                    return next_id
            after_id = await run_in_threadpool(cleanup)
            ticks += 1
        except SQLAlchemyError as exc:
            logging.getLogger('api.live_map.chat').warning('Chat cleanup postponed (%s)', type(exc).__name__)


@asynccontextmanager
async def chat_lifespan(app):
    task = asyncio.create_task(chat_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
