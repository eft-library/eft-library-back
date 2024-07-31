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
                hideouts = []
                for row in result:
                    hideout_dict = {
                        "master_id": row[0],
                        "master_name_en": row[1],
                        "master_name_kr": row[2],
                        "image": row[3],
                        "data": row[4],
                    }
                    hideouts.append(hideout_dict)

                return hideouts
        except Exception as e:
            print("오류 발생:", e)
            return None
