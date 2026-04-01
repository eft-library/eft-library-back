from sqlalchemy import text
from api.map.models import Map, MapV3
from api.map.util import MapUtil
from database import DataBaseConnector, V3Database
import logging

logger = logging.getLogger("api.map")


class MapService:
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
            "is_use": map_data.is_use,
            "name_en": map_data.name_en,
            "name_ko": map_data.name_ko,
            "name_ja": map_data.name_ja,
            "parent_map_id": map_data.parent_map_id,
            "map_depth": map_data.map_depth,
            "mot_image_en": map_data.mot_image_en,
            "mot_image_ko": map_data.mot_image_ko,
            "mot_image_ja": map_data.mot_image_ja,
            "three_image": map_data.three_image,
            "three_json": map_data.three_json,
        }

    # TODO: 삭제 예정
    @staticmethod
    def get_map(map_id: str):
        """
        ID를 통한 map 조회
        """
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(MapUtil.get_map_detail_query())
                param = {"map_id": map_id}
                result = s.execute(query, param)
                map_data = [dict(row) for row in result.mappings()]

                map_selector = (
                    s.query(Map).filter(Map.depth == 1).order_by(Map.order).all()
                )

                map_selector_list = [
                    {"id": m.id, "name": m.name, "link": m.link} for m in map_selector
                ]

                return {
                    "map": map_data[0],  # 상세 정보
                    "map_selector": map_selector_list,  # selector 목록
                }

        except Exception as e:
            logger.error(
                f"get_map: {map_id}, error: {e}",
                exc_info=True,
            )
            return None

    # TODO: 삭제 예정
    @staticmethod
    def get_sub_map(map_id: str):
        """
        ID를 통한 sub map 조회
        """
        try:

            with DataBaseConnector.SessionLocal() as s:
                response_map = (
                    s.query(Map)
                    .filter(Map.parent_value == map_id)
                    .order_by(Map.order)
                    .all()
                )
                return response_map
        except Exception as e:
            logger.error(
                f"get_sub_map: {map_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_map_by_normalized_name(normalized_name: str):
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
                    MapService._serialize_top_level_map_v3(row)
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
                    "map": MapService._serialize_map_v3(map_data),
                    "top_level_map": top_level_maps,
                    "related_maps": related_maps,
                }

        except Exception as e:
            logger.error(
                f"get_map_by_normalized_name: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
