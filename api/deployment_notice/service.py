import logging
from datetime import datetime

import pytz

from api.deployment_notice.models import DeploymentNotice
from database import Database

logger = logging.getLogger("api.deployment_notice")


class DeploymentNoticeService:
    NOTICE_ID = "frontend-deploy"
    DEFAULT_MESSAGE_KO = "곧 웹사이트 배포로 접속이 일시적으로 끊길 수 있습니다."
    DEFAULT_MESSAGE_EN = "The website may briefly disconnect soon due to deployment."
    DEFAULT_MESSAGE_JA = "まもなくサイトのデプロイにより一時的に接続が切れる可能性があります。"

    @staticmethod
    def _now():
        return datetime.now(pytz.timezone("Asia/Seoul"))

    @staticmethod
    def _is_notice_active(notice: DeploymentNotice):
        if not notice.is_active:
            return False

        now = DeploymentNoticeService._now()
        start_time = notice.start_time
        end_time = notice.end_time
        if start_time is not None and start_time.tzinfo is None:
            start_time = pytz.timezone("Asia/Seoul").localize(start_time)
        if end_time is not None and end_time.tzinfo is None:
            end_time = pytz.timezone("Asia/Seoul").localize(end_time)

        if start_time is not None and now < start_time:
            return False
        if end_time is not None and now > end_time:
            return False
        return True

    @staticmethod
    def _serialize_notice(notice: DeploymentNotice | None):
        if notice is None:
            return {
                "isActive": False,
                "messageKo": DeploymentNoticeService.DEFAULT_MESSAGE_KO,
                "messageEn": DeploymentNoticeService.DEFAULT_MESSAGE_EN,
                "messageJa": DeploymentNoticeService.DEFAULT_MESSAGE_JA,
                "startTime": None,
                "endTime": None,
                "updateTime": None,
            }

        return {
            "isActive": DeploymentNoticeService._is_notice_active(notice),
            "messageKo": notice.message_ko
            or DeploymentNoticeService.DEFAULT_MESSAGE_KO,
            "messageEn": notice.message_en
            or DeploymentNoticeService.DEFAULT_MESSAGE_EN,
            "messageJa": notice.message_ja
            or DeploymentNoticeService.DEFAULT_MESSAGE_JA,
            "startTime": notice.start_time,
            "endTime": notice.end_time,
            "updateTime": notice.update_time,
        }

    @staticmethod
    def get_deployment_notice():
        try:
            with Database.SessionLocal() as s:
                notice = (
                    s.query(DeploymentNotice)
                    .filter(DeploymentNotice.id == DeploymentNoticeService.NOTICE_ID)
                    .first()
                )
                return DeploymentNoticeService._serialize_notice(notice)
        except Exception as e:
            logger.error(f"get_deployment_notice_v3 error: {e}", exc_info=True)
            return None
