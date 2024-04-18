from sqlalchemy.orm import joinedload
from api.menu.models import MainMenu, SubMenu
from database import DataBaseConnector


class MenuService:
    @staticmethod
    def get_all_menu():
        session = DataBaseConnector.create_session()
        main_menu_list = session.query(MainMenu).options(joinedload(MainMenu.sub_menus)).order_by(MainMenu.main_menu_order).all()
        session.close()
        return main_menu_list
