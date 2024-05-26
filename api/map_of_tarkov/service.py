from api.boss.models import Boss
from api.map.models import Map
from api.map_of_tarkov.models import Extraction
from database import DataBaseConnector
import os
from dotenv import load_dotenv


class MapOfTarkovService:
    @staticmethod
    def get_map_of_tarkov(map_id):
        """
        map of tarkov 지도 조회
        """
        try:
            load_dotenv()
            session = DataBaseConnector.create_session()
            boss_list = (
                session.query(Boss).filter(Boss.boss_spawn.contains([map_id])).all()
            )

            updated_boss_list = []
            for boss in boss_list:
                if boss.boss_location_guide is not None:
                    boss.boss_location_guide = boss.boss_location_guide.replace(
                        "/tkw_quest", os.getenv("NAS_DATA") + "/tkw_quest"
                    )
                updated_boss_list.append(boss)

            # 각각의 Boss 객체를 딕셔너리로 변환
            combined_info = [boss.__dict__ for boss in updated_boss_list]

            map_info = session.query(Map).filter(Map.map_id == map_id).first()

            extraction_info = (
                session.query(Extraction)
                .filter(Extraction.extraction_map == map_id)
                .first()
            )

            map_of_tarkov = {
                "boss_list": combined_info,
                "map_info": map_info,
                "extraction_info": extraction_info,
            }

            session.close()
            return map_of_tarkov
        except Exception as e:
            print("오류 발생:", e)
            return None
