from sqlalchemy.orm import subqueryload

from api.community.util import CommunityUtil
from api.dynamic_info.models import DynamicInfo
from api.home.models import MenuGroup, MainInfo
from database import DataBaseConnector
from sqlalchemy import text


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

                side_issue_posts_query = text(CommunityUtil.get_posts_with_issue())
                get_side_issue_posts = s.execute(
                    side_issue_posts_query,
                    {"limit": 5, "offset": 0, "user_email": None},
                )
                get_side_issue_posts_data = [
                    dict(row) for row in get_side_issue_posts.mappings()
                ]

                news_data = (
                    s.query(DynamicInfo).filter(DynamicInfo.id == "NEWS_COLUMN").first()
                )

                main_info["main_info"] = main_info_list
                main_info["menu"] = main_menu_list
                main_info["news"] = news_data
                main_info["issue_posts"] = get_side_issue_posts_data

                return main_info
        except Exception as e:
            print("오류 발생:", e)
            return None
