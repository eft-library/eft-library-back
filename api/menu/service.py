from sqlalchemy.orm import subqueryload
from api.menu.models import MainMenu, MainInfo
from database import DataBaseConnector


class MenuService:
    @staticmethod
    def get_all_menu():
        session = DataBaseConnector.create_session()
        main_menu_list = (session
                          .query(MainMenu)
                          .options(subqueryload(MainMenu.sub_menus))
                          .order_by(MainMenu.order).all())
        session.close()
        return main_menu_list

    @staticmethod
    def get_main_info():
        session = DataBaseConnector.create_session()
        main_info_list = (session
                          .query(MainInfo)
                          .order_by(MainInfo.order).all())
        session.close()
        return main_info_list
