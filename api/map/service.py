from sqlalchemy import text
from sqlalchemy.orm import subqueryload

from api.map.models import Map
from api.map.util import MapUtil
from database import DataBaseConnector


class MapService:
    @staticmethod
    def get_map(map_id: str):
        """
        ID를 통한 map 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(MapUtil.get_map_detail_query())
                param = {"map_id": map_id}
                result = s.execute(query, param)
                map = [dict(row) for row in result.mappings()]

                map_selector = (
                    s.query(Map).filter(Map.depth == 1).order_by(Map.order).all()
                )

                map_selector_list = [
                    {"id": m.id, "name": m.name, "link": m.link} for m in map_selector
                ]

                return {
                    "map": map[0],  # 상세 정보
                    "map_selector": map_selector_list,  # selector 목록
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_sub_map(map_id: str):
        """
        ID를 통한 sub map 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                response_map = (
                    s.query(Map)
                    .filter(Map.parent_value == map_id)
                    .order_by(Map.order)
                    .all()
                )
                return response_map
        except Exception as e:
            print("오류 발생:", e)
            return None
