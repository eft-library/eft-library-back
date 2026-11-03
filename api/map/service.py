from api.map.models import Map
from database import Database
import logging

logger = logging.getLogger("api.map")


class MapService:
    @staticmethod
    def _serialize_top_level_map(map_data: Map):
        return {
            "normalized_name": map_data.normalized_name,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
        }

    @staticmethod
    def _serialize_map(map_data: Map):
        return {
            "id": map_data.id,
            "normalized_name": map_data.normalized_name,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
            "three_image": map_data.three_image,
            "three_json": map_data.three_json,
        }

    @staticmethod
    def get_map_by_normalized_name(normalized_name: str):
        try:
            with Database.SessionLocal() as s:
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

                related_parent_id = None
                if map_data.map_depth == 1:
                    related_parent_id = map_data.id
                elif map_data.map_depth == 2:
                    related_parent_id = map_data.parent_map_id

                top_level_maps = [
                    MapService._serialize_top_level_map(row)
                    for row in s.query(Map)
                    .filter(
                        Map.map_depth == 1,
                        Map.is_use.is_(True),
                    )
                    .order_by(Map.sort_order)
                    .all()
                ]

                related_maps = []
                if related_parent_id is not None:
                    related_maps = [
                        {
                            "normalized_name": row.normalized_name,
                            "name_en": row.name_en,
                            "name_ko": row.name_ko,
                            "name_ja": row.name_ja,
                        }
                        for row in s.query(
                            Map.normalized_name,
                            Map.name_en,
                            Map.name_ko,
                            Map.name_ja,
                        )
                        .filter(
                            Map.parent_map_id == related_parent_id,
                            Map.is_use.is_(True),
                        )
                        .order_by(Map.sort_order)
                        .all()
                    ]

                return {
                    "map": MapService._serialize_map(map_data),
                    "top_level_map": top_level_maps,
                    "related_maps": related_maps,
                }

        except Exception as e:
            logger.error(
                f"get_map_by_normalized_name_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
