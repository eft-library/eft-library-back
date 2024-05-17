from api.weapon.models import Weapon
from database import DataBaseConnector


class WeaponService:
    @staticmethod
    def get_all_weapon():
        session = DataBaseConnector.create_session()
        weapon_list = (session
                        .query(Weapon)
                        .all())
        session.close()
        return weapon_list

