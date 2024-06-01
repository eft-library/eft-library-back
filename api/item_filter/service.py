from sqlalchemy.orm import subqueryload

from api.item_filter.models import FilterCategories
from database import DataBaseConnector


class ItemFilterService:

    @staticmethod
    def get_all_item_filter():
        """
        item filter 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            maps = (session
                    .query(FilterCategories)
                    .options(subqueryload(FilterCategories.sub))
                    .all())
            session.close()
            return maps
        except Exception as e:
            print("오류 발생:", e)
            return None