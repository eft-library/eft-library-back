from sqlalchemy.orm import subqueryload

from api.map.models import  ParentMap
from database import DataBaseConnector


class MapService:
    @staticmethod
    def get_map(map_id: str):
        """
        ID를 통한 map 조회
        """
        session = DataBaseConnector.create_session()
        response_map = session.query(ParentMap).options(subqueryload(ParentMap.sub)).filter(ParentMap.id == map_id).first()
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
                    .options(subqueryload(ParentMap.sub))
                    .order_by(ParentMap.order)
                    .all())
            session.close()

            for parent_map in maps:
                parent_map.sub.sort(key=lambda x: x.order)

            return maps
        except Exception as e:
            print("오류 발생:", e)
            return None
