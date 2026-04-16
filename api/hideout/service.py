from typing import List
from sqlalchemy import text
from database import DataBaseConnector, V3Database
from api.hideout.util import HideoutUtil
from api.hideout.query import HideoutQueryV3
from datetime import datetime
from api.hideout.hideout_res_models import UserHideOut
from api.hideout.hideout_req_models import ItemType
import pytz
import logging

logger = logging.getLogger("api.hideout")


class HideoutService:
    @staticmethod
    def get_station(user_email: str | None):
        try:

            with DataBaseConnector.SessionLocal() as s:
                user_hideout = {}

                # 은신처 기본 정보
                hideout_query = text(HideoutUtil.get_hideout_query())
                hideouts = s.execute(hideout_query).mappings().all()
                user_hideout["hideout_info"] = list(hideouts)

                # 완료 레벨 목록
                user_info = None
                if user_email:
                    user_info = (
                        s.query(UserHideOut)
                        .filter(UserHideOut.user_email == user_email)
                        .first()
                    )

                user_hideout["complete_list"] = (
                    user_info.complete_list if user_info else []
                )

                user_hideout["item_list"] = user_info.item_list if user_info else []

                # 아이템 필요 정보
                item_require_query = text(HideoutUtil.get_item_require_info())
                item_require = (
                    s.execute(item_require_query, {"user_email": user_email})
                    .mappings()
                    .all()
                )
                user_hideout["item_require_info"] = list(item_require)

                return user_hideout

        except Exception as e:
            logger.error(
                f"get_station error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _group_rows_by_key(rows, key):
        grouped = {}
        for row in rows:
            row_dict = dict(row)
            grouped.setdefault(row_dict[key], []).append(row_dict)
        return grouped


class HideoutServiceV3:
    @staticmethod
    def _group_rows_by_key(rows, key):
        grouped = {}
        for row in rows:
            row_dict = dict(row)
            grouped.setdefault(row_dict[key], []).append(row_dict)
        return grouped

    @staticmethod
    def get_station_by_normalized_name_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                master_sql = text(HideoutQueryV3.hideout_master_sql())
                levels_sql = text(HideoutQueryV3.hideout_levels_sql())

                master = (
                    s.execute(master_sql, {"normalized_name": normalized_name})
                    .mappings()
                    .first()
                )
                if master is None:
                    return None

                level_rows = (
                    s.execute(levels_sql, {"master_id": master["id"]}).mappings().all()
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
    def save_station(complete_list: List[str], user_email: str):
        try:

            with DataBaseConnector.SessionLocal() as s:
                user_hideout = (
                    s.query(UserHideOut).filter_by(user_email=user_email).first()
                )
                utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                kst = pytz.timezone("Asia/Seoul")
                kst_now = utc_now.astimezone(kst)

                if user_hideout:
                    user_hideout.complete_list = complete_list
                    user_hideout.update_time = kst_now
                    s.commit()
                else:
                    new_user_hideout = UserHideOut(
                        user_email=user_email,
                        item_list=[],
                        complete_list=complete_list,
                        update_time=kst_now,
                    )
                    s.add(new_user_hideout)
                    s.commit()
                return HideoutService.get_station(user_email)
        except Exception as e:
            logger.error(
                f"save_station: {complete_list}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def save_station_item(item_list: List[ItemType], user_email: str):
        try:

            item_list_json = [item.model_dump() for item in item_list]

            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
            kst_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))

            with DataBaseConnector.SessionLocal() as s:
                user_hideout = (
                    s.query(UserHideOut).filter_by(user_email=user_email).first()
                )

                if user_hideout:
                    user_hideout.item_list = item_list_json
                    user_hideout.update_time = kst_now
                else:
                    user_hideout = UserHideOut(
                        user_email=user_email,
                        item_list=item_list_json,
                        complete_list=[],
                        update_time=kst_now,
                    )
                    s.add(user_hideout)

                s.commit()
                return user_hideout

        except Exception as e:
            logger.error(
                f"save_station_item: {item_list}, error: {e}",
                exc_info=True,
            )
            return None
