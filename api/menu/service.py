from sqlalchemy.orm import subqueryload
from api.home.models import MenuGroup, MainInfo
from api.search.models import Search
from database import DataBaseConnector
import logging

logger = logging.getLogger("api.menu")


class MenuService:
    @staticmethod
    def get_all_menu():
        try:
            with DataBaseConnector.SessionLocal() as s:
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.order)
                    .all()
                )
                return main_menu_list
        except Exception as e:
            logger.error(
                f"get_all_menu error: {e}",
                exc_info=True,
            )
            return None

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
    def get_main_info():
        try:
            with DataBaseConnector.SessionLocal() as s:
                main_info_list = s.query(MainInfo).order_by(MainInfo.order).all()
                return main_info_list
        except Exception as e:
            logger.error(
                f"get_main_info error: {e}",
                exc_info=True,
            )
            return None
