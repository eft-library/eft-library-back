from sqlalchemy.orm import subqueryload

from api.community.util import CommunityUtil
from api.dynamic_info.models import DynamicInfo
from api.home.models import MenuGroup, MainInfo
from api.home.query import HomeQuery
from database import DataBaseConnector, V3Database
from sqlalchemy import text
import logging

logger = logging.getLogger("api.home")


class MenuService:

    @staticmethod
    def get_main():
        try:
            main_info = {}
            with DataBaseConnector.SessionLocal() as s:
                main_info_list = s.query(MainInfo).order_by(MainInfo.order).all()
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.order)
                    .all()
                )

                side_home_posts_query = text(CommunityUtil.get_home_post())
                get_side_home_posts = s.execute(side_home_posts_query)
                get_side_home_posts_data = [
                    dict(row) for row in get_side_home_posts.mappings()
                ]

                news_data = (
                    s.query(DynamicInfo).filter(DynamicInfo.id == "NEWS_COLUMN").first()
                )

                main_info["main_info"] = main_info_list
                main_info["menu"] = main_menu_list
                main_info["news"] = news_data
                main_info["home_posts"] = get_side_home_posts_data

                return main_info
        except Exception as e:
            logger.error(
                f"get_main error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_home():
        try:
            main_info = {}
            with V3Database.SessionLocal() as s:
                main_contents_query = text(HomeQuery.main_contents_sql())
                menu_groups_query = text(HomeQuery.menu_groups_sql())
                menu_sub_groups_query = text(HomeQuery.menu_sub_groups_sql())
                news_items_query = text(HomeQuery.news_item_sql())

                main_info_list = s.execute(main_contents_query).mappings().all()
                menu_groups = s.execute(menu_groups_query).mappings().all()
                menu_sub_groups = s.execute(menu_sub_groups_query).mappings().all()
                news_data = s.execute(news_items_query).mappings().all()

                sub_menus_by_parent = {}
                for row in menu_sub_groups:
                    parent_group_id = row["parent_group_id"]
                    sub_menus_by_parent.setdefault(parent_group_id, []).append(
                        dict(row)
                    )

                main_menu_list = []
                for row in menu_groups:
                    menu = dict(row)
                    menu["sub_menus"] = sub_menus_by_parent.get(menu["id"], [])
                    main_menu_list.append(menu)

                side_home_posts_query = text(CommunityUtil.get_home_post())
                get_side_home_posts = s.execute(side_home_posts_query)
                get_side_home_posts_data = [
                    dict(row) for row in get_side_home_posts.mappings()
                ]

                main_info["main_info"] = [dict(row) for row in main_info_list]
                main_info["menu"] = main_menu_list
                main_info["news"] = [dict(row) for row in news_data]
                main_info["home_posts"] = get_side_home_posts_data

                return main_info
        except Exception as e:
            logger.error(
                f"get_main_v3 error: {e}",
                exc_info=True,
            )
            return None
