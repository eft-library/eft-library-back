from sqlalchemy import text

from api.hideout.hideout_req_models import ItemTypeV3
from api.hideout.hideout_res_models import UserHideoutV3
from api.hideout.query import HideoutQueryV3
from database import V3Database
from datetime import datetime
from typing import List, Optional
import logging
import json

logger = logging.getLogger("api.hideout")


class HideoutServiceV3:
    @staticmethod
    def _group_rows_by_key(rows, key):
        grouped = {}
        for row in rows:
            row_dict = dict(row)
            grouped.setdefault(row_dict[key], []).append(row_dict)
        return grouped

    @staticmethod
    def get_station_v3(user_email: Optional[str]):
        try:
            with V3Database.SessionLocal() as s:
                result = {
                    "user_hideout": None,
                    "hideout_list": [],
                }

                if user_email:
                    user_hideout = (
                        s.query(UserHideoutV3)
                        .filter(UserHideoutV3.email == user_email)
                        .first()
                    )
                    if user_hideout:
                        result["user_hideout"] = {
                            "email": user_hideout.email,
                            "complete_list": user_hideout.complete_list or [],
                            "item_list": user_hideout.item_list or [],
                            "update_time": user_hideout.update_time,
                        }
                    else:
                        result["user_hideout"] = {
                            "email": user_email,
                            "complete_list": [],
                            "item_list": [],
                            "update_time": None,
                        }

                hideout_master_rows = (
                    s.execute(text(HideoutQueryV3.hideout_master_list_sql()))
                    .mappings()
                    .all()
                )
                result["hideout_list"] = [dict(row) for row in hideout_master_rows]
                return result
        except Exception as e:
            logger.error(f"get_station_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_station_by_normalized_name_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                master = (
                    s.execute(
                        text(HideoutQueryV3.hideout_master_sql()),
                        {"normalized_name": normalized_name},
                    )
                    .mappings()
                    .first()
                )
                if master is None:
                    return None

                level_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_levels_sql()),
                        {"master_id": master["id"]},
                    )
                    .mappings()
                    .all()
                )
                levels = [dict(row) for row in level_rows]
                if not levels:
                    return {"master": dict(master), "levels": []}

                level_ids = [level["id"] for level in levels]

                trader_require_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_trader_require_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )
                item_require_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_item_require_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )
                station_require_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_station_require_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )
                bonus_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_bonus_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )
                skill_require_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_skill_require_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )
                craft_rows = (
                    s.execute(
                        text(HideoutQueryV3.hideout_crafts_sql()),
                        {"level_ids": level_ids},
                    )
                    .mappings()
                    .all()
                )

                crafts = [dict(row) for row in craft_rows]
                craft_ids = [craft["id"] for craft in crafts]
                craft_require_rows = []
                if craft_ids:
                    craft_require_rows = (
                        s.execute(
                            text(HideoutQueryV3.hideout_craft_require_items_sql()),
                            {"craft_ids": craft_ids},
                        )
                        .mappings()
                        .all()
                    )

                trader_require_by_level = HideoutServiceV3._group_rows_by_key(
                    trader_require_rows, "hideout_level_id"
                )
                item_require_by_level = HideoutServiceV3._group_rows_by_key(
                    item_require_rows, "hideout_level_id"
                )
                station_require_by_level = HideoutServiceV3._group_rows_by_key(
                    station_require_rows, "hideout_level_id"
                )
                bonus_by_level = HideoutServiceV3._group_rows_by_key(
                    bonus_rows, "hideout_level_id"
                )
                skill_require_by_level = HideoutServiceV3._group_rows_by_key(
                    skill_require_rows, "hideout_level_id"
                )
                craft_require_by_craft = HideoutServiceV3._group_rows_by_key(
                    craft_require_rows, "craft_id"
                )

                crafts_by_level = {}
                for craft in crafts:
                    craft["require_items"] = craft_require_by_craft.get(craft["id"], [])
                    crafts_by_level.setdefault(craft["hideout_level_id"], []).append(
                        craft
                    )

                level_details = []
                for level in levels:
                    level_details.append(
                        {
                            **level,
                            "trader_require": trader_require_by_level.get(
                                level["id"], []
                            ),
                            "item_require": item_require_by_level.get(level["id"], []),
                            "station_require": station_require_by_level.get(
                                level["id"], []
                            ),
                            "skill_require": skill_require_by_level.get(
                                level["id"], []
                            ),
                            "bonus": bonus_by_level.get(level["id"], []),
                            "crafts": crafts_by_level.get(level["id"], []),
                        }
                    )

                return {
                    "master": dict(master),
                    "levels": level_details,
                }

        except Exception as e:
            logger.error(
                f"get_station_by_normalized_name_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def save_station_v3(complete_list: List[str], user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                s.execute(
                    text(HideoutQueryV3.upsert_user_hideout_complete_list_sql()),
                    {
                        "email": user_email,
                        "complete_list": complete_list,
                        "update_time": datetime.utcnow(),
                    },
                )
                s.commit()
                return HideoutServiceV3.get_station_v3(user_email)
        except Exception as e:
            logger.error(
                f"save_station_v3: {complete_list}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def save_station_item_v3(item_list: List[ItemTypeV3], user_email: str):
        try:
            item_list_json = [item.model_dump() for item in item_list]

            with V3Database.SessionLocal() as s:
                s.execute(
                    text(
                        HideoutQueryV3.upsert_user_hideout_item_list_preserve_complete_sql()
                    ),
                    {
                        "email": user_email,
                        "item_list": json.dumps(item_list_json),
                        "update_time": datetime.utcnow(),
                    },
                )
                s.commit()
                return HideoutServiceV3.get_station_v3(user_email)
        except Exception as e:
            logger.error(
                f"save_station_item_v3: {item_list}, error: {e}",
                exc_info=True,
            )
            return None
