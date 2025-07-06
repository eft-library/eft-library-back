from sqlalchemy.orm import subqueryload

from api.dynamic_info.models import DynamicInfo
from api.home.models import MenuGroup, MainInfo
from database import DataBaseConnector


class MenuService:

    @staticmethod
    def get_main():
        try:
            session = DataBaseConnector.create_session_factory()
            main_info = {}
            with session() as s:
                main_info_list = s.query(MainInfo).order_by(MainInfo.order).all()
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.order)
                    .all()
                )
                news_data = (
                    s.query(DynamicInfo).filter(DynamicInfo.id == "NEWS_COLUMN").first()
                )

                main_info['main_info'] = main_info_list
                main_info['menu'] = main_menu_list
                main_info['news'] = news_data
                return main_info
        except Exception as e:
            print("오류 발생:", e)
            return None
