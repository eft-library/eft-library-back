from sqlalchemy.orm import subqueryload

from api.item_filter.models import FilterCategories, FilterSubCategories
from database import DataBaseConnector


class ItemFilterService:

    @staticmethod
    def get_all_item_filter():
        """
        item filter 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                item_filter = (
                    s.query(FilterCategories)
                    .options(subqueryload(FilterCategories.sub))
                    .all()
                )
                return item_filter
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_sub_item_filter_categories():
        """
        item filter sub 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                sub_item_filter = s.query(FilterSubCategories).all()

                return sub_item_filter
        except Exception as e:
            print("오류 발생:", e)
            return None
