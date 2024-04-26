from sqlalchemy.orm import subqueryload

from api.map.models import Map, ParentMap
from database import DataBaseConnector


class MapService:
    @staticmethod
    def get_map(map_id: str):
        """
        ID를 통한 map 조회
        """
        session = DataBaseConnector.create_session()
        response_map = session.query(Map).filter(Map.map_id == map_id).first()
        session.close()
        return response_map

    @staticmethod
    def get_all_map():
        """
        map 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            maps = (session
                    .query(ParentMap)
                    .options(subqueryload(ParentMap.map_sub))
                    .order_by(ParentMap.map_order)
                    .all())
            session.close()

            for parent_map in maps:
                parent_map.map_sub.sort(key=lambda x: x.map_order)

            return maps
        except Exception as e:
            print("오류 발생:", e)
            return None
