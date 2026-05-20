from copy import deepcopy

from sqlalchemy import nullslast, text

from api.live_map.models import LiveMapFloorV3, LiveMapStaticPointV3
from api.live_map.query import LiveMapQueryV3
from api.map.models import MapV3
from api.quest.service import QuestServiceV3
from database import V3Database
import logging

logger = logging.getLogger("api.live_map")


class LiveMapServiceV3:
    @staticmethod
    def _serialize_map_selector_v3(row: dict):
        return {
            "id": row["id"],
            "normalized_name": row["normalized_name"],
            "name_en": row["name_en"],
            "name_ko": row["name_ko"],
            "name_ja": row["name_ja"],
        }

    @staticmethod
    def _serialize_floor_v3(floor: LiveMapFloorV3):
        return {
            "id": floor.id,
            "map_id": floor.map_id,
            "floor_no": floor.floor_no,
            "name_en": floor.name_en,
            "name_ko": floor.name_ko,
            "name_ja": floor.name_ja,
            "image": floor.image,
            "min_z": floor.min_z,
            "max_z": floor.max_z,
        }

    @staticmethod
    def _serialize_static_point_v3(point: LiveMapStaticPointV3):
        return {
            "id": point.id,
            "map_id": point.map_id,
            "floor_id": point.floor_id,
            "floor_no": point.floor_no,
            "category": point.category,
            "name_en": point.name_en,
            "name_ko": point.name_ko,
            "name_ja": point.name_ja,
            "description_en": point.description_en,
            "description_ko": point.description_ko,
            "description_ja": point.description_ja,
            "x": point.x,
            "z": point.z,
            "y": point.y,
            "metadata": point.metadata_,
        }

    @staticmethod
    def _strip_quest_html_text_v3(quest_detail: dict | None):
        if quest_detail is None:
            return None

        quest = quest_detail.get("quest")
        if quest is not None:
            quest.pop("guide_en", None)
            quest.pop("guide_ko", None)
            quest.pop("guide_ja", None)
        return quest_detail

    @staticmethod
    def _attach_live_map_point_to_objective_v3(
        row: dict, details: list[dict], quest_detail: dict | None
    ):
        if quest_detail is None:
            return None

        quest_info = deepcopy(quest_detail)
        objective_id = row["objective_id"]
        if objective_id is None:
            return quest_info

        live_map_point = {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "details": details,
        }

        for objective in quest_info.get("objectives", []):
            if objective.get("objective_id") == objective_id:
                objective["live_map_point"] = live_map_point
                break

        return quest_info

    @staticmethod
    def _serialize_quest_point_v3(row: dict, quest_info: dict | None):
        return {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "quest_info": quest_info,
        }

    @staticmethod
    def _get_map_selector_v3(s):
        return [
            LiveMapServiceV3._serialize_map_selector_v3(dict(row))
            for row in s.execute(text(LiveMapQueryV3.map_selector_sql())).mappings()
        ]

    @staticmethod
    def get_live_map_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                map_data = (
                    s.query(MapV3)
                    .filter(
                        MapV3.normalized_name == normalized_name,
                        MapV3.is_use.is_(True),
                    )
                    .first()
                )
                if map_data is None:
                    return None

                floors = (
                    s.query(LiveMapFloorV3)
                    .filter(LiveMapFloorV3.map_id == map_data.id)
                    .order_by(
                        nullslast(LiveMapFloorV3.sort_order),
                        LiveMapFloorV3.floor_no,
                    )
                    .all()
                )

                static_points = (
                    s.query(LiveMapStaticPointV3)
                    .filter(LiveMapStaticPointV3.map_id == map_data.id)
                    .order_by(
                        LiveMapStaticPointV3.floor_no,
                        LiveMapStaticPointV3.category,
                        LiveMapStaticPointV3.sort_order,
                        LiveMapStaticPointV3.name_en,
                    )
                    .all()
                )

                detail_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.point_details_by_map_sql()),
                        {"map_id": map_data.id},
                    ).mappings()
                ]
                details_by_point_id = {}
                for detail in detail_rows:
                    details_by_point_id.setdefault(detail["point_id"], []).append(
                        {
                            "id": detail["id"],
                            "description_en": detail["description_en"],
                            "description_ko": detail["description_ko"],
                            "description_ja": detail["description_ja"],
                            "image": detail["image"],
                        }
                    )

                quest_point_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.quest_points_by_map_sql()),
                        {"map_id": map_data.id},
                    ).mappings()
                ]

                quest_detail_by_normalized_name = {}
                for row in quest_point_rows:
                    quest_normalized_name = row["quest_normalized_name"]
                    if (
                        quest_normalized_name is not None
                        and quest_normalized_name not in quest_detail_by_normalized_name
                    ):
                        quest_detail_by_normalized_name[quest_normalized_name] = (
                            LiveMapServiceV3._strip_quest_html_text_v3(
                                QuestServiceV3.get_quest_by_normalized_name_v3(
                                    quest_normalized_name
                                )
                            )
                        )

                quest_points = [
                    LiveMapServiceV3._serialize_quest_point_v3(
                        row,
                        LiveMapServiceV3._attach_live_map_point_to_objective_v3(
                            row,
                            details_by_point_id.get(row["id"], []),
                            quest_detail_by_normalized_name.get(
                                row["quest_normalized_name"]
                            ),
                        ),
                    )
                    for row in quest_point_rows
                ]

                return {
                    "map_selector": LiveMapServiceV3._get_map_selector_v3(s),
                    "floors": [
                        LiveMapServiceV3._serialize_floor_v3(row) for row in floors
                    ],
                    "quest_points": quest_points,
                    "static_points": [
                        LiveMapServiceV3._serialize_static_point_v3(row)
                        for row in static_points
                    ],
                }
        except Exception as e:
            logger.error(
                f"get_live_map_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
