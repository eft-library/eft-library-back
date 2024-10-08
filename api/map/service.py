from sqlalchemy.orm import subqueryload

from api.map.models import Map, ParentMap
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
                response_map = (
                    s.query(ParentMap)
                    .options(subqueryload(ParentMap.sub))
                    .filter(ParentMap.id == map_id)
                    .first()
                )
                return response_map
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_map():
        """
        map 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                maps = (
                    s.query(ParentMap)
                    .options(subqueryload(ParentMap.sub))
                    .order_by(ParentMap.order)
                    .all()
                )

            for parent_map in maps:
                parent_map.sub.sort(key=lambda x: x.order)

            return maps
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
