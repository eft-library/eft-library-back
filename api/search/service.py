from api.search.models import Search
from database import DataBaseConnector


class SearchService:
    @staticmethod
    def get_all_search():
        """
        검색 정보 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                search_list = s.query(Search).order_by(Search.order).all()
                return search_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_site_list():
        """
        사이트 정보 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                search_list = s.query(Search).with_entities(Search.link).distinct().order_by(Search.link).all()
                return [link for link, in search_list]
        except Exception as e:
            print("오류 발생:", e)
            return None