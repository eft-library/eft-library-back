from sqlalchemy.orm import subqueryload

from api.home.models import (
    MainInfo,
    MenuGroup,
    NewsItem,
)
from api.home.query import HomeQuery
from api.search.models import AutocompleteItem
from database import Database
from sqlalchemy import text
import logging

logger = logging.getLogger("api.home")


class HomeService:
    NEWS_TYPES = (
        "patch",
        "event",
        "next_update",
        "recommend",
        "tarkov_info",
        "notice",
    )

    @staticmethod
    def _serialize_main_info(main_info: MainInfo):
        return {
            "id": main_info.id,
            "name_en": main_info.name_en,
            "name_ko": main_info.name_ko,
            "name_ja": main_info.name_ja,
            "url": main_info.url,
            "image": main_info.image,
        }

    @staticmethod
    def _serialize_menu_sub_group(sub_menu):
        return {
            "id": sub_menu.id,
            "name_en": sub_menu.name_en,
            "name_ko": sub_menu.name_ko,
            "name_ja": sub_menu.name_ja,
            "parent_group_id": sub_menu.parent_group_id,
            "url": sub_menu.url,
        }

    @staticmethod
    def _serialize_menu_group(menu_group: MenuGroup):
        return {
            "id": menu_group.id,
            "name_en": menu_group.name_en,
            "name_ko": menu_group.name_ko,
            "name_ja": menu_group.name_ja,
            "sub_menus": [
                HomeService._serialize_menu_sub_group(sub_menu)
                for sub_menu in menu_group.sub_menus
            ],
        }

    @staticmethod
    def _serialize_news_item(news_item: NewsItem):
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
    def _group_news_items(news_items: list[NewsItem]):
        grouped_news = {news_type: [] for news_type in HomeService.NEWS_TYPES}

        for news_item in news_items:
            news_type = news_item.news_type
            if news_type not in grouped_news:
                grouped_news[news_type] = []
            grouped_news[news_type].append(
                HomeService._serialize_news_item(news_item)
            )

        return grouped_news

    @staticmethod
    def _serialize_autocomplete_item(item: AutocompleteItem):
        return {
            "url": item.url,
            "autocomplete_text_en": item.autocomplete_text_en,
            "autocomplete_text_ko": item.autocomplete_text_ko,
            "autocomplete_text_ja": item.autocomplete_text_ja,
        }

    @staticmethod
    def get_home():
        try:
            main_info = {}
            with Database.SessionLocal() as s:
                main_info_list = (
                    s.query(MainInfo).order_by(MainInfo.sort_order).all()
                )
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.sort_order)
                    .all()
                )
                news_data = (
                    s.query(NewsItem)
                    .filter(NewsItem.is_active.is_(True))
                    .order_by(NewsItem.sort_order)
                    .all()
                )

                side_home_posts_query = text(HomeQuery.home_posts_sql())
                get_side_home_posts = s.execute(side_home_posts_query)
                get_side_home_posts_data = [
                    dict(row) for row in get_side_home_posts.mappings()
                ]

                main_info["main"] = [
                    HomeService._serialize_main_info(row) for row in main_info_list
                ]
                main_info["menu"] = [
                    HomeService._serialize_menu_group(row)
                    for row in main_menu_list
                ]
                main_info["news"] = HomeService._group_news_items(news_data)
                main_info["home_posts"] = get_side_home_posts_data

                return main_info
        except Exception as e:
            logger.error(
                f"get_home_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_home_posts():
        try:
            with Database.SessionLocal() as s:
                home_posts_query = text(HomeQuery.home_posts_sql())
                home_posts = s.execute(home_posts_query)
                return [dict(row) for row in home_posts.mappings()]
        except Exception as e:
            logger.error(
                f"get_home_posts_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_menu_with_autocomplete():
        try:
            with Database.SessionLocal() as s:
                main_menu_list = (
                    s.query(MenuGroup)
                    .options(subqueryload(MenuGroup.sub_menus))
                    .order_by(MenuGroup.sort_order)
                    .all()
                )
                search_list = (
                    s.query(AutocompleteItem)
                    .order_by(AutocompleteItem.sort_order)
                    .all()
                )

                return {
                    "nav_list": [
                        HomeService._serialize_menu_group(row)
                        for row in main_menu_list
                    ],
                    "autocomplete_items": [
                        HomeService._serialize_autocomplete_item(row)
                        for row in search_list
                    ],
                }
        except Exception as e:
            logger.error(
                f"get_menu_with_autocomplete_v3 error: {e}",
                exc_info=True,
            )
            return None
