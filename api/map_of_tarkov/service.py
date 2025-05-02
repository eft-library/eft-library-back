from sqlalchemy import text

from api.boss.models import Boss
from api.map.models import Map
from api.map_of_tarkov.models import Extraction, Transits, WhereAmI
from api.map_of_tarkov.util import MapOfTarkovUtil
from database import DataBaseConnector


class MapOfTarkovService:
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

                query = text(MapOfTarkovUtil.get_map_of_tarkov_detail_query())
                param = {"map_id": map_id}
                result = s.execute(query, param)
                map_data = [dict(row) for row in result.mappings()]

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

                # boss_list

            map_of_tarkov = {
                "map_info": map_data[0],
                "extraction_info": extraction_info,
                "transits_info": transits_info,
                "map_id": map_id,
                "find_info": find_info,
                "map_selector": map_selector_list,
            }

            return map_of_tarkov
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_map_of_tarkov():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 모든 지도 정보와 관련 데이터를 한번에 가져오기
                maps = s.query(Map).all()
                bosses = s.query(Boss).all()
                extractions = s.query(Extraction).all()
                transits = s.query(Transits).all()
                finds = s.query(WhereAmI).all()

            # 지도 ID를 기준으로 데이터 분류
            boss_dict = {}
            for boss in bosses:
                for spawn_map_id in boss.spawn:  # Boss.spawn이 리스트라고 가정
                    boss_dict.setdefault(spawn_map_id, []).append(boss)

            extraction_dict = {}
            for extraction in extractions:
                extraction_dict.setdefault(extraction.map, []).append(extraction)

            transits_dict = {}
            for transit in transits:
                transits_dict.setdefault(transit.map, []).append(transit)

            find_dict = {}
            for find in finds:
                find_dict.setdefault(find.id, []).append(find)

            # 최종 결과 구성
            result = []
            for map_info in maps:
                map_id = map_info.id

                updated_boss_list = []
                for boss in boss_dict.get(map_id, []):
                    updated_boss_list.append(boss.__dict__)

                map_of_tarkov = {
                    "boss_list": updated_boss_list,
                    "map_info": map_info,
                    "extraction_info": extraction_dict.get(map_id, []),
                    "transits_info": transits_dict.get(map_id, []),
                    "map_id": map_id,
                    "find_info": find_dict.get(map_id, []),
                }

                result.append(map_of_tarkov)

            return result
        except Exception as e:
            print("오류 발생:", e)
            return None
