import logging
from datetime import datetime

import pytz

from api.deployment_notice.models import DeploymentNoticeV3
from database import V3Database

logger = logging.getLogger("api.deployment_notice")


class DeploymentNoticeServiceV3:
    NOTICE_ID = "frontend-deploy"
    DEFAULT_MESSAGE_KO = "곧 웹사이트 배포로 접속이 일시적으로 끊길 수 있습니다."
    DEFAULT_MESSAGE_EN = "The website may briefly disconnect soon due to deployment."
    DEFAULT_MESSAGE_JA = "まもなくサイトのデプロイにより一時的に接続が切れる可能性があります。"

    @staticmethod
    def _now_v3():
        return datetime.now(pytz.timezone("Asia/Seoul"))

    @staticmethod
    def _is_notice_active_v3(notice: DeploymentNoticeV3):
        if not notice.is_active:
            return False

        now = DeploymentNoticeServiceV3._now_v3()
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
    def _serialize_notice_v3(notice: DeploymentNoticeV3 | None):
        if notice is None:
            return {
                "isActive": False,
                "messageKo": DeploymentNoticeServiceV3.DEFAULT_MESSAGE_KO,
                "messageEn": DeploymentNoticeServiceV3.DEFAULT_MESSAGE_EN,
                "messageJa": DeploymentNoticeServiceV3.DEFAULT_MESSAGE_JA,
                "startTime": None,
                "endTime": None,
                "updateTime": None,
            }

        return {
            "isActive": DeploymentNoticeServiceV3._is_notice_active_v3(notice),
            "messageKo": notice.message_ko
            or DeploymentNoticeServiceV3.DEFAULT_MESSAGE_KO,
            "messageEn": notice.message_en
            or DeploymentNoticeServiceV3.DEFAULT_MESSAGE_EN,
            "messageJa": notice.message_ja
            or DeploymentNoticeServiceV3.DEFAULT_MESSAGE_JA,
            "startTime": notice.start_time,
            "endTime": notice.end_time,
            "updateTime": notice.update_time,
        }

    @staticmethod
    def get_deployment_notice_v3():
        try:
            with V3Database.SessionLocal() as s:
                notice = (
                    s.query(DeploymentNoticeV3)
                    .filter(DeploymentNoticeV3.id == DeploymentNoticeServiceV3.NOTICE_ID)
                    .first()
                )
                return DeploymentNoticeServiceV3._serialize_notice_v3(notice)
        except Exception as e:
            logger.error(f"get_deployment_notice_v3 error: {e}", exc_info=True)
            return None
