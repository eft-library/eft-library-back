from sqlalchemy.orm import subqueryload
from api.home.models import MenuGroup
from api.menu.query import MenuQuery
from api.search.models import Search
from database import DataBaseConnector, V3Database
from sqlalchemy import text
import logging

logger = logging.getLogger("api.menu")


class MenuService:

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
    def get_menu_with_autocomplete():
        try:
            with V3Database.SessionLocal() as s:
                menu_groups_query = text(MenuQuery.menu_groups_sql())
                menu_sub_groups_query = text(MenuQuery.menu_sub_groups_sql())
                autocomplete_items_query = text(MenuQuery.autocomplete_items_sql())

                menu_groups = s.execute(menu_groups_query).mappings().all()
                menu_sub_groups = s.execute(menu_sub_groups_query).mappings().all()
                search_list = s.execute(autocomplete_items_query).mappings().all()

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

                menu_with_search = {
                    "main_menu_list": main_menu_list,
                    "search_list": [dict(row) for row in search_list],
                }
                return menu_with_search
        except Exception as e:
            logger.error(
                f"get_menu_with_search_v3 error: {e}",
                exc_info=True,
            )
            return None
