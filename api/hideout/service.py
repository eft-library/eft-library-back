from sqlalchemy import text
from database import DataBaseConnector
from api.hideout.util import HideoutUtil


class HideoutService:
    @staticmethod
    def get_all_hideout():
        """
        hideout 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(HideoutUtil.get_hideout_query())
                result = s.execute(query)
                hideouts = [dict(row) for row in result.mappings()]
                return hideouts
        except Exception as e:
            print("오류 발생:", e)
            return None
