from sqlalchemy.orm import subqueryload
from api.home.models import AutocompleteItemV3, MenuGroup, MenuGroupV3
from api.search.models import Search
from database import DataBaseConnector, V3Database
import logging

logger = logging.getLogger("api.menu")


class MenuService:

    @staticmethod
    def get_menu_with_search():
        try:
            with DataBaseConnector.SessionLocal() as s:
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.order)
                    .all()
                )
                search_list = s.query(Search).order_by(Search.order).all()
                menu_with_search = {
                    "main_menu_list": main_menu_list,
                    "search_list": search_list,
                }
                return menu_with_search
        except Exception as e:
            logger.error(
                f"get_menu_with_search error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_menu_with_autocomplete():
        try:
            with V3Database.SessionLocal() as s:
                main_menu_list = (
                    s.query(MenuGroupV3)
                    .options(subqueryload(MenuGroupV3.sub_menus))
                    .order_by(MenuGroupV3.sort_order)
                    .all()
                )
                search_list = (
                    s.query(AutocompleteItemV3)
                    .order_by(AutocompleteItemV3.sort_order)
                    .all()
                )

                menu_with_search = {
                    "main_menu_list": main_menu_list,
                    "search_list": search_list,
                }
                return menu_with_search
        except Exception as e:
            logger.error(
                f"get_menu_with_search_v3 error: {e}",
                exc_info=True,
            )
            return None
