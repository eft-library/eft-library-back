from api.boss.models import Boss
from database import DataBaseConnector
import os
from dotenv import load_dotenv


class BossService:
    @staticmethod
    def get_all_boss():
        """
        boss 전체 조회
        """
        try:
            load_dotenv()
            session = DataBaseConnector.create_session()
            boss_list = session.query(Boss).all()

            updated_boss_list = []
            for boss in boss_list:
                if boss.boss_location_guide is not None:
                    boss.boss_location_guide = boss.boss_location_guide.replace(
                        "/tkw_quest", os.getenv("NAS_DATA") + "/tkw_quest"
                    )
                updated_boss_list.append(boss)

            # 각각의 Boss 객체를 딕셔너리로 변환
            combined_info = [boss.__dict__ for boss in updated_boss_list]

            session.close()
            return combined_info
        except Exception as e:
            print("오류 발생:", e)
            return None
