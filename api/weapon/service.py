from api.weapon.models import Weapon, Knife, Throwable
from database import DataBaseConnector


class WeaponService:
    @staticmethod
    def get_all_weapon():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                weapon_list = {
                    "gun": s.query(Weapon).all(),
                    "knife": s.query(Knife).all(),
                    "throwable": s.query(Throwable).all(),
                }
            return weapon_list
        except Exception as e:
            print("오류 발생:", e)
            return None
