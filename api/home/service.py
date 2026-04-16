from sqlalchemy.orm import subqueryload

from api.community.util import CommunityUtil
from api.home.models import (
    AutocompleteItemV3,
    MainInfoV3,
    MenuGroupV3,
    NewsItemV3,
)
from database import V3Database
from sqlalchemy import text
import logging

logger = logging.getLogger("api.home")


class HomeServiceV3:
    NEWS_TYPES = (
        "patch",
        "event",
        "next_update",
        "recommend",
        "tarkov_info",
        "notice",
    )

    @staticmethod
    def _serialize_main_info_v3(main_info: MainInfoV3):
        return {
            "id": main_info.id,
            "name_en": main_info.name_en,
            "name_ko": main_info.name_ko,
            "name_ja": main_info.name_ja,
            "url": main_info.url,
            "image": main_info.image,
        }

    @staticmethod
    def _serialize_menu_sub_group_v3(sub_menu):
        return {
            "id": sub_menu.id,
            "name_en": sub_menu.name_en,
            "name_ko": sub_menu.name_ko,
            "name_ja": sub_menu.name_ja,
            "parent_group_id": sub_menu.parent_group_id,
            "url": sub_menu.url,
        }

    @staticmethod
    def _serialize_menu_group_v3(menu_group: MenuGroupV3):
        return {
            "id": menu_group.id,
            "name_en": menu_group.name_en,
            "name_ko": menu_group.name_ko,
            "name_ja": menu_group.name_ja,
            "sub_menus": [
                HomeServiceV3._serialize_menu_sub_group_v3(sub_menu)
                for sub_menu in menu_group.sub_menus
            ],
        }

    @staticmethod
    def _serialize_news_item_v3(news_item: NewsItemV3):
        return {
            "id": news_item.id,
            "news_type": news_item.news_type,
            "title_en": news_item.title_en,
            "title_ko": news_item.title_ko,
            "title_ja": news_item.title_ja,
            "link": news_item.link,
            "is_new": news_item.is_new,
            "is_renewal": news_item.is_renewal,
        }

    @staticmethod
    def _group_news_items_v3(news_items: list[NewsItemV3]):
        grouped_news = {news_type: [] for news_type in HomeServiceV3.NEWS_TYPES}

        for news_item in news_items:
            news_type = news_item.news_type
            if news_type not in grouped_news:
                grouped_news[news_type] = []
            grouped_news[news_type].append(
                HomeServiceV3._serialize_news_item_v3(news_item)
            )

        return grouped_news

    @staticmethod
    def _serialize_autocomplete_item_v3(item: AutocompleteItemV3):
        return {
            "url": item.url,
            "autocomplete_text_en": item.autocomplete_text_en,
            "autocomplete_text_ko": item.autocomplete_text_ko,
            "autocomplete_text_ja": item.autocomplete_text_ja,
        }

    @staticmethod
    def get_home_v3():
        try:
            main_info = {}
            with V3Database.SessionLocal() as s:
                main_info_list = (
                    s.query(MainInfoV3).order_by(MainInfoV3.sort_order).all()
                )
                main_menu_list = (
                    s.query(MenuGroupV3)
                    .options(subqueryload(MenuGroupV3.sub_menus))
                    .order_by(MenuGroupV3.sort_order)
                    .all()
                )
                news_data = (
                    s.query(NewsItemV3)
                    .filter(NewsItemV3.is_active.is_(True))
                    .order_by(NewsItemV3.sort_order)
                    .all()
                )

                side_home_posts_query = text(CommunityUtil.get_home_post())
                get_side_home_posts = s.execute(side_home_posts_query)
                get_side_home_posts_data = [
                    dict(row) for row in get_side_home_posts.mappings()
                ]

                main_info["main"] = [
                    HomeServiceV3._serialize_main_info_v3(row) for row in main_info_list
                ]
                main_info["menu"] = [
                    HomeServiceV3._serialize_menu_group_v3(row)
                    for row in main_menu_list
                ]
                main_info["news"] = HomeServiceV3._group_news_items_v3(news_data)
                main_info["home_posts"] = get_side_home_posts_data

                return main_info
        except Exception as e:
            logger.error(
                f"get_home_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_menu_with_autocomplete_v3():
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

                return {
                    "nav_list": [
                        HomeServiceV3._serialize_menu_group_v3(row)
                        for row in main_menu_list
                    ],
                    "autocomplete_items": [
                        HomeServiceV3._serialize_autocomplete_item_v3(row)
                        for row in search_list
                    ],
                }
        except Exception as e:
            logger.error(
                f"get_menu_with_autocomplete_v3 error: {e}",
                exc_info=True,
            )
            return None
