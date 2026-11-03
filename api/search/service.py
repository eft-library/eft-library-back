from sqlalchemy import desc

from api.search.models import AutocompleteItem, Sitemap
from database import Database
import logging

logger = logging.getLogger("api.search")


class SearchService:
    @staticmethod
    def _serialize_autocomplete_item(item: AutocompleteItem):
        return {
            "url": item.url,
            "autocomplete_text_en": item.autocomplete_text_en,
            "autocomplete_text_ko": item.autocomplete_text_ko,
            "autocomplete_text_ja": item.autocomplete_text_ja,
            "category": item.category,
            "sort_order": item.sort_order,
            "update_time": item.update_time,
        }

    @staticmethod
    def _serialize_sitemap(sitemap: Sitemap):
        return {
            "id": sitemap.id,
            "url": sitemap.url,
            "priority": (
                float(sitemap.priority) if sitemap.priority is not None else None
            ),
            "change_freq": sitemap.change_freq,
            "sitemap_value": sitemap.sitemap_value,
            "create_time": sitemap.create_time,
            "update_time": sitemap.update_time,
        }

    @staticmethod
    def get_all_search():
        """
        V3 검색 자동완성 정보 전체 조회
        """
        try:
            with Database.SessionLocal() as s:
                search_list = (
                    s.query(AutocompleteItem)
                    .order_by(AutocompleteItem.sort_order)
                    .all()
                )
                return [
                    SearchService._serialize_autocomplete_item(item)
                    for item in search_list
                ]
        except Exception as e:
            logger.error(
                f"get_all_search_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_site_list():
        """
        V3 사이트 정보 전체 조회
        """
        try:
            with Database.SessionLocal() as s:
                sitemap_list = (
                    s.query(Sitemap).order_by(desc(Sitemap.priority)).all()
                )
                return [
                    SearchService._serialize_sitemap(sitemap)
                    for sitemap in sitemap_list
                ]
        except Exception as e:
            logger.error(
                f"get_all_site_list_v3 error: {e}",
                exc_info=True,
            )
            return None
