from api.where_am_i.res_models import UserLocationRequestV3
from database import V3Database
from sqlalchemy import text
from api.where_am_i.req_models import LogLocationRequestV3, RaidStateRequestV3, ReqWhereAmI
from util.websocket import send_wpf_location, send_wpf_log_location, send_wpf_raid_state
import logging

logger = logging.getLogger("api.where_am_i")


class WhereAmIServiceV3:
    @staticmethod
    def check_wpf_user_v3(user_email):
        try:
            with V3Database.SessionLocal() as s:
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
    async def send_location_v3(req: ReqWhereAmI):
        exists_user = WhereAmIServiceV3.check_wpf_user_v3(req.email)
        try:
            if exists_user:
                with V3Database.SessionLocal() as s:
                    user_location = UserLocationRequestV3(
                        email=req.email,
                        location=req.location,
                    )

                    s.add(user_location)
                    s.commit()
                    await send_wpf_location(user_email=req.email, location=req.location)
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
    async def send_raid_state_v3(req: RaidStateRequestV3):
        try:
            if not WhereAmIServiceV3.check_wpf_user_v3(req.email):
                logger.warning(
                    "send_raid_state_v3 존재하지 않는 사용자: email=%r",
                    req.email,
                )
                return None

            await send_wpf_raid_state(
                user_email=req.email,
                state=req.model_dump(mode="json", exclude={"email"}),
            )
            return True
        except Exception as e:
            logger.error(
                f"send_raid_state_v3: {req.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    async def send_log_location_v3(req: LogLocationRequestV3):
        try:
            if not WhereAmIServiceV3.check_wpf_user_v3(req.email):
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
