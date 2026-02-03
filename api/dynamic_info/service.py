from api.dynamic_info.models import DynamicInfo
from database import DataBaseConnector
import logging

logger = logging.getLogger("api.dynamic")


class DynamicInfoService:

    @staticmethod
    def get_column(column_key: str):
        """
        column 전체 조회
        """
        try:

            with DataBaseConnector.SessionLocal() as s:
                column_list = (
                    s.query(DynamicInfo).filter(DynamicInfo.id == column_key).first()
                )
                return column_list
        except Exception as e:
            logger.error(
                f"get_column: {column_key}, error: {e}",
                exc_info=True,
            )
        return None
