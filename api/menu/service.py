from sqlalchemy.orm import joinedload, subqueryload
from api.menu.models import MainMenu, SubMenu
from database import DataBaseConnector


class MenuService:
    @staticmethod
    def get_all_menu():
        session = DataBaseConnector.create_session()
        main_menu_list = (session
                          .query(MainMenu)
                          .options(subqueryload(MainMenu.sub_menus))
                          .order_by(MainMenu.main_menu_order).all())
        session.close()
        return main_menu_list
