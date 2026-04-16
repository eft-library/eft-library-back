from api.map.models import MapV3
from database import V3Database
import logging

logger = logging.getLogger("api.map")


class MapServiceV3:
    @staticmethod
    def _serialize_top_level_map_v3(map_data: MapV3):
        return {
            "normalized_name": map_data.normalized_name,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
        }

    @staticmethod
    def _serialize_map_v3(map_data: MapV3):
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
    def get_map_by_normalized_name_v3(normalized_name: str):
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

                related_parent_id = None
                if map_data.map_depth == 1:
                    related_parent_id = map_data.id
                elif map_data.map_depth == 2:
                    related_parent_id = map_data.parent_map_id

                top_level_maps = [
                    MapServiceV3._serialize_top_level_map_v3(row)
                    for row in s.query(MapV3)
                    .filter(
                        MapV3.map_depth == 1,
                        MapV3.is_use.is_(True),
                    )
                    .order_by(MapV3.sort_order)
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
                            MapV3.normalized_name,
                            MapV3.name_en,
                            MapV3.name_ko,
                            MapV3.name_ja,
                        )
                        .filter(
                            MapV3.parent_map_id == related_parent_id,
                            MapV3.is_use.is_(True),
                        )
                        .order_by(MapV3.sort_order)
                        .all()
                    ]

                return {
                    "map": MapServiceV3._serialize_map_v3(map_data),
                    "top_level_map": top_level_maps,
                    "related_maps": related_maps,
                }

        except Exception as e:
            logger.error(
                f"get_map_by_normalized_name_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
