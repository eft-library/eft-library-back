from api.weapon.models import Weapon, Knife, Throwable
from database import DataBaseConnector


class WeaponService:
    @staticmethod
    def get_all_weapon():
        session = DataBaseConnector.create_session()
        gun_list = session.query(Weapon).all()
        knife_list = session.query(Knife).all()
        throwable_list = session.query(Throwable).all()
        weapon_list = {
            "gun": gun_list,
            "knife": knife_list,
            "throwable": throwable_list,
        }
        session.close()
        return weapon_list
