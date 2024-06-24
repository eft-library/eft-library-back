from api.weapon.models import Weapon, Knife, Throwable
from database import DataBaseConnector


class WeaponService:
    @staticmethod
    def get_all_weapon():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                gun_list = s.query(Weapon).all()
                knife_list = s.query(Knife).all()
                throwable_list = s.query(Throwable).all()
            weapon_list = {
                "gun": gun_list,
                "knife": knife_list,
                "throwable": throwable_list,
            }
            return weapon_list
        except Exception as e:
            print("오류 발생:", e)
            return None
