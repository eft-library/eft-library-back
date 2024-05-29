from api.search.models import Search
from database import DataBaseConnector


class SearchService:
    @staticmethod
    def get_all_search():
        """
        검색 정보 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            search_list = session.query(Search).order_by(Search.search_order).all()
            session.close()

            return search_list
        except Exception as e:
            print("오류 발생:", e)
            return None
