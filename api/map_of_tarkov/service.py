from sqlalchemy import text
from api.map.models import Map
from api.map_of_tarkov.models import MapPoint
from api.map_of_tarkov.query import MapOfTarkovQuery
from database import Database
import logging

logger = logging.getLogger("api.mot")


class MapOfTarkovService:
    @staticmethod
    def _serialize_map_selector(map_data: Map):
        return {
            "normalized_name": map_data.normalized_name,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
        }

    @staticmethod
    def _serialize_map_detail(map_data: Map):
        return {
            "id": map_data.id,
            "normalized_name": map_data.normalized_name,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
            "mot_image_en": map_data.mot_image_en,
            "mot_image_ko": map_data.mot_image_ko,
            "mot_image_ja": map_data.mot_image_ja,
        }

    @staticmethod
    def _serialize_map_point(point: MapPoint):
        return {
            "id": point.id,
            "point_type": point.point_type,
            "name_en": point.name_en,
            "name_ko": point.name_ko,
            "name_ja": point.name_ja,
            "is_unlimited_use": point.is_unlimited_use,
            "is_one_time_use": point.is_one_time_use,
            "image": point.image,
            "faction": point.faction,
            "map_id": point.map_id,
            "requirements_en": point.requirements_en,
            "requirements_ko": point.requirements_ko,
            "requirements_ja": point.requirements_ja,
            "tip_en": point.tip_en,
            "tip_ko": point.tip_ko,
            "tip_ja": point.tip_ja,
        }

    @staticmethod
    def _serialize_boss_info(boss_row: dict, followers: list[dict]):
        return {
            "id": boss_row["id"],
            "name_en": boss_row["name_en"],
            "name_ko": boss_row["name_ko"],
            "name_ja": boss_row["name_ja"],
            "faction": boss_row["faction"],
            "image": boss_row["image"],
            "normalized_name": boss_row["normalized_name"],
            "health_total": boss_row["health_total"],
            "health_image": boss_row["health_image"],
            "head_hp": boss_row["head_hp"],
            "thorax_hp": boss_row["thorax_hp"],
            "stomach_hp": boss_row["stomach_hp"],
            "left_arm_hp": boss_row["left_arm_hp"],
            "right_arm_hp": boss_row["right_arm_hp"],
            "left_leg_hp": boss_row["left_leg_hp"],
            "right_leg_hp": boss_row["right_leg_hp"],
            "spawn_chance": boss_row["spawn_chance"],
            "followers": followers,
        }

    @staticmethod
    def get_map_of_tarkov(normalized_name: str):
        try:
            with Database.SessionLocal() as s:
                boss_info_query = text(MapOfTarkovQuery.boss_info_by_map_sql())
                boss_followers_query = text(
                    MapOfTarkovQuery.boss_followers_by_parent_ids_sql()
                )

                map_data = (
                    s.query(Map)
                    .filter(
                        Map.normalized_name == normalized_name,
                        Map.is_use.is_(True),
                    )
                    .first()
                )
                if map_data is None:
                    return None

                map_selector = (
                    s.query(Map)
                    .filter(
                        Map.map_depth == 1,
                        Map.is_use.is_(True),
                    )
                    .order_by(Map.sort_order)
                    .all()
                )

                related_parent_id = None
                if map_data.map_depth == 1:
                    related_parent_id = map_data.id
                elif map_data.map_depth == 2:
                    related_parent_id = map_data.parent_map_id

                child_maps = []
                if related_parent_id is not None:
                    child_maps = (
                        s.query(Map)
                        .filter(
                            Map.parent_map_id == related_parent_id,
                            Map.is_use.is_(True),
                        )
                        .order_by(Map.sort_order)
                        .all()
                    )

                map_points = (
                    s.query(MapPoint)
                    .filter(MapPoint.map_id == map_data.id)
                    .order_by(MapPoint.sort_order)
                    .all()
                )

                boss_rows = (
                    s.execute(boss_info_query, {"map_id": map_data.id}).mappings().all()
                )
                boss_ids = [row["id"] for row in boss_rows]

                followers_by_parent = {}
                if boss_ids:
                    follower_rows = (
                        s.execute(boss_followers_query, {"boss_ids": boss_ids})
                        .mappings()
                        .all()
                    )
                    for row in follower_rows:
                        parent_boss_id = row["parent_boss_id"]
                        followers_by_parent.setdefault(parent_boss_id, []).append(
                            {
                                "id": row["id"],
                                "name_en": row["name_en"],
                                "name_ko": row["name_ko"],
                                "name_ja": row["name_ja"],
                                "normalized_name": row["normalized_name"],
                            }
                        )

                extraction_info = []
                transit_info = []
                for point in map_points:
                    serialized_point = MapOfTarkovService._serialize_map_point(
                        point
                    )
                    if point.point_type == "extraction":
                        extraction_info.append(serialized_point)
                    elif point.point_type == "transit":
                        transit_info.append(serialized_point)

                return {
                    "map_info": MapOfTarkovService._serialize_map_detail(map_data),
                    "map_selector": [
                        MapOfTarkovService._serialize_map_selector(row)
                        for row in map_selector
                    ],
                    "child_maps": [
                        MapOfTarkovService._serialize_map_selector(row)
                        for row in child_maps
                    ],
                    "extraction_info": extraction_info,
                    "transit_info": transit_info,
                    "boss_info": [
                        MapOfTarkovService._serialize_boss_info(
                            dict(row), followers_by_parent.get(row["id"], [])
                        )
                        for row in boss_rows
                    ],
                }

        except Exception as e:
            logger.error(
                f"get_map_of_tarkov_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
