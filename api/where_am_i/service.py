from api.where_am_i.res_models import UserLocationRequest
from database import Database
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .map_resolution import resolve_map_slug
from fastapi import HTTPException
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool
from api.where_am_i.req_models import LogLocationRequest, RaidStateRequest, ReqWhereAmI
from util.location_socket import (
    send_wpf_location as send_wpf_location,
    send_wpf_log_location as send_wpf_log_location,
    send_wpf_raid_state as send_wpf_raid_state,
)
import logging

logger = logging.getLogger("api.where_am_i")


class WhereAmIService:
    @staticmethod
    def check_wpf_user(user_email):
        try:
            with Database.SessionLocal() as s:
                result = s.execute(
                    text("select exists(select 1 from user_info where email = :email)"),
                    {"email": user_email},
                ).scalar()
                return result
        except Exception as e:
            logger.error(
                f"check_wpf_user_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    async def send_location(req: ReqWhereAmI):
        exists_user = WhereAmIService.check_wpf_user(req.email)
        try:
            if exists_user:
                with Database.SessionLocal() as s:
                    user_location = UserLocationRequest(
                        email=req.email,
                        location=req.location,
                    )

                    s.add(user_location)
                    s.flush()
                    request_id = user_location.id
                    s.commit()
                    logger.info('location_stored request_id=%s', request_id)
                    await send_wpf_location(user_email=req.email, location=req.location,
                                            request_id=request_id)
                    return True
            else:
                logger.warning(
                    "send_location_v3 존재하지 않는 사용자: email=%r",
                    req.email,
                )
                return None
        except Exception as e:
            logger.error(
                f"send_location_v3: {req.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    async def send_raid_state(req: RaidStateRequest, analytics_context=None):
        exists = await run_in_threadpool(WhereAmIService.check_wpf_user, req.email)
        if exists is None:
            raise HTTPException(503, 'RAID_STATE_DATABASE_UNAVAILABLE')
        if not exists:
            raise HTTPException(404, 'USER_NOT_FOUND')
        try:
            map_slug = await run_in_threadpool(resolve_map_slug, req.map)
        except SQLAlchemyError as error:
            logger.warning('Raid map resolution unavailable (%s)', type(error).__name__)
            raise HTTPException(503, 'RAID_MAP_LOOKUP_UNAVAILABLE') from None
        if analytics_context is not None:
            analytics_context.update(map_resolved=True, map_slug=map_slug)
        if req.raid_ends_at is not None and map_slug is None:
            raise HTTPException(422, 'RAID_MAP_UNRESOLVED')
        connection_state = req.model_dump(mode='json', exclude={'email'})
        connection_state['map'] = map_slug
        try:
            event_id = await send_wpf_raid_state(
                user_email=req.email,
                state=connection_state,
            )
            if analytics_context is not None:
                analytics_context['event_id'] = event_id
            return True
        except RedisError as error:
            logger.warning('Raid state publish unavailable (%s)', type(error).__name__)
            raise HTTPException(503, 'RAID_STATE_PUBLISH_UNAVAILABLE') from None

    @staticmethod
    async def send_log_location(req: LogLocationRequest):
        try:
            if not WhereAmIService.check_wpf_user(req.email):
                logger.warning(
                    "send_log_location_v3 존재하지 않는 사용자: email=%r",
                    req.email,
                )
                return None

            await send_wpf_log_location(
                user_email=req.email,
                location=req.model_dump(mode="json", exclude={"email"}),
            )
            return True
        except Exception as e:
            logger.error(
                f"send_log_location_v3: {req.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
