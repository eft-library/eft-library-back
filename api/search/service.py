from api.search.models import Search
from database import DataBaseConnector
import os
from dotenv import load_dotenv
from sqlalchemy import text
from api.search.util import SearchUtil


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
        load_dotenv()

        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(SearchUtil.get_sitemap_query())
                result = s.execute(query)

                search_list = [os.getenv("SITE_URL")]
                for row in result:
                    search_list.append(os.getenv("SITE_URL") + row[0])

                return search_list
        except Exception as e:
            print("오류 발생:", e)
            return None
