from sqlalchemy.orm import subqueryload
from api.home.models import MenuGroup, MainInfo
from api.search.models import Search
from database import DataBaseConnector


class MenuService:
    @staticmethod
    def get_all_menu():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.order)
                    .all()
                )
                return main_menu_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_menu_with_search():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
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
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_main_info():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                main_info_list = s.query(MainInfo).order_by(MainInfo.order).all()
                return main_info_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_main_slide():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                main_info_list = (
                    s.query(MainInfo)
                    .order_by(MainInfo.order)
                    .filter(MainInfo.use_slide.is_(True))
                    .all()
                )
                return main_info_list
        except Exception as e:
            print("오류 발생:", e)
            return None
