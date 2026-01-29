from sqlalchemy import desc

from api.search.models import Search, Sitemap
from database import DataBaseConnector
from dotenv import load_dotenv
import logging

logger = logging.getLogger("api.search")


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
            logger.error(
                f"get_all_search error: {e}",
                exc_info=True,
            )
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
                sitemap_list = s.query(Sitemap).order_by(desc(Sitemap.priority)).all()
                return sitemap_list
        except Exception as e:
            logger.error(
                f"get_all_site_list error: {e}",
                exc_info=True,
            )
            return None
