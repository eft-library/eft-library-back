from api.boss.models import Boss
from database import DataBaseConnector


class BossService:
    @staticmethod
    def get_all_boss():
        """
        boss 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            boss_list = session.query(Boss).all()

            # boss map 추가
            for boss in boss_list:
                boss_spawn = []
                for spawn in boss.boss_location_spawn_chance_en:
                    boss_spawn.append(spawn["location"])
                setattr(boss, "boss_spawn", boss_spawn)
            session.close()
            return boss_list
        except Exception as e:
            print("오류 발생:", e)
            return None
