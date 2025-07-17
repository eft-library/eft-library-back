from sqlalchemy import text
from api.map.models import Map
from api.map_of_tarkov.models import Extraction, Transits, WhereAmI
from api.map_of_tarkov.util import MapOfTarkovUtil
from database import DataBaseConnector


class MapOfTarkovService:

    @staticmethod
    def get_map_selector():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                maps = s.query(Map).filter(Map.depth == 1).order_by(Map.order).all()
            return [{"id": m.id, "name": m.name} for m in maps]
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_map_info(map_id):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                map_query = text(MapOfTarkovUtil.get_map_of_tarkov_detail_query())
                map_param = {"map_id": map_id}
                map_result = s.execute(map_query, map_param)
                map_data = [dict(row) for row in map_result.mappings()]
            return map_data[0]
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_boss_info(map_id):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss_query = text(MapOfTarkovUtil.get_map_of_tarkov_boss_query())
                boss_param = {"map_id": map_id}
                boss_result = s.execute(boss_query, boss_param)
                boss_data = [dict(row) for row in boss_result.mappings()]
            return boss_data
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_extraction_info(map_id):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                extractions = (
                    s.query(Extraction)
                    .filter(Extraction.map == map_id)
                    .order_by(Extraction.faction, Extraction.name)
                    .all()
                )
            return extractions
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_transits_info(map_id):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                transits = (
                    s.query(Transits)
                    .filter(Transits.map == map_id)
                    .order_by(Transits.faction, Transits.name)
                    .all()
                )
            return transits
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_find_info(map_id):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                find_info = s.query(WhereAmI).filter(WhereAmI.id == map_id).first()
            return find_info
        except Exception as e:
            print("오류 발생:", e)
            return None
    @staticmethod
    def get_map_of_tarkov(map_id):
        """
        map of tarkov 지도 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                map_selector = (
                    s.query(Map).filter(Map.depth == 1).order_by(Map.order).all()
                )
                map_selector_list = [{"id": m.id, "name": m.name} for m in map_selector]

                map_query = text(MapOfTarkovUtil.get_map_of_tarkov_detail_query())
                map_param = {"map_id": map_id}
                map_result = s.execute(map_query, map_param)
                map_data = [dict(row) for row in map_result.mappings()]

                boss_query = text(MapOfTarkovUtil.get_map_of_tarkov_boss_query())
                boss_param = {"map_id": map_id}
                boss_result = s.execute(boss_query, boss_param)
                boss_data = [dict(row) for row in boss_result.mappings()]

                extraction_info = (
                    s.query(Extraction)
                    .filter(Extraction.map == map_id)
                    .order_by(Extraction.faction, Extraction.name)
                    .all()
                )
                transits_info = (
                    s.query(Transits)
                    .filter(Transits.map == map_id)
                    .order_by(Transits.faction, Transits.name)
                    .all()
                )

                find_info = s.query(WhereAmI).filter(WhereAmI.id == map_id).first()

            map_of_tarkov = {
                "map_info": map_data[0],
                "extraction_info": extraction_info,
                "transits_info": transits_info,
                "map_id": map_id,
                "find_info": find_info,
                "map_selector": map_selector_list,
                "boss_info": boss_data,
            }

            return map_of_tarkov
        except Exception as e:
            print("오류 발생:", e)
            return None