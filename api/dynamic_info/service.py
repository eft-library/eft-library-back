from api.dynamic_info.models import DynamicInfo
from database import DataBaseConnector


class DynamicInfoService:

    @staticmethod
    def get_column(column_key: str):
        """
        column 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                column_list = (
                    s.query(DynamicInfo).filter(DynamicInfo.id == column_key).first()
                )
                return column_list
        except Exception as e:
            print("get_column 오류:", e)
        return None
