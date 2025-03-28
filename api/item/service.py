from api.item.models import (
    Headwear,
    Rig,
    Throwable,
    Weapon,
    FaceCover,
    Knife,
    Item
)
from api.item.util import ItemUtil
from database import DataBaseConnector
from sqlalchemy import desc, text, cast, Numeric, func


class ItemService:
    @staticmethod
    def get_item_list(item_type: str):
        """
        item 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                item_list = s.query(Item).filter(Item.category == item_type).order_by(cast(Item.info["class_value"], Numeric)).all()
                return item_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_headset():
        """
        headset 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headset = s.query(Item).filter(Item.category == 'Headset').order_by(cast(func.coalesce(Item.info["class_value"], "0"), Numeric)).all()
                return headset
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_weapon():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                weapon_list = {
                    "gun": s.query(Item).filter(Item.category == 'Gun').all(),
                    "knife": s.query(Item).filter(Item.category == 'Knife').all(),
                    "throwable": s.query(Item).filter(Item.category == 'Throwable').all(),
                }
            return weapon_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_headwear():
        """
        headwear 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headwear = s.query(Item).filter(Item.category == 'Headwear').order_by(cast(func.coalesce(Item.info["class_value"], "0"), Numeric)).all()

            class_headwear = []

            no_class_headwear = []

            for wear in headwear:
                if wear.info['class_value'] is None:
                    no_class_headwear.append(wear)
                else:
                    class_headwear.append(wear)

            result_headwear = {
                "class_headwear": [item.__dict__ for item in class_headwear],
                "no_class_headwear": [item.__dict__ for item in no_class_headwear],
            }

            return result_headwear
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_armor_vest():
        """
        armor vest 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                armor_vest = s.query(Item).filter(Item.category == 'ArmorVest').order_by(cast(func.coalesce(Item.info["class_value"], "0"), Numeric)).all()
                return armor_vest
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_backpack():
        """
        backpack 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                backpack = s.query(Item).filter(Item.category == 'Backpack').order_by(cast(func.coalesce(Item.info["capacity"], "0"), Numeric)).all()
                return backpack
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_container():
        """
        container 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                container = s.query(Item).filter(Item.category == 'Container').order_by(cast(func.coalesce(Item.info["capacity"], "0"), Numeric)).all()
                return container
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_key():
        """
        key 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_key_query())
                result = s.execute(query)
                key = [dict(row) for row in result.mappings()]
                return key
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_rig():
        """
        rig 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rig = s.query(Item).filter(Item.category == 'Rig').order_by(cast(func.coalesce(Item.info["class_value"], "0"), Numeric), cast(func.coalesce(Item.info["class_value"], "0"), Numeric)).all()
            class_rig = []
            no_class_rig = []

            for item in rig:
                if item.class_value is None:
                    no_class_rig.append(item)
                else:
                    class_rig.append(item)

            result_rig = {
                "class_rig": [item.__dict__ for item in class_rig],
                "no_class_rig": [item.__dict__ for item in no_class_rig],
            }

            return result_rig
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_provisions():
        """
        provisions 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_provisions_query())
                result = s.execute(query)
                provisions = [dict(row) for row in result.mappings()]
                return provisions
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_medical():
        """
        medical 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                medical = s.query(Item).filter(Item.category == 'Medical').order_by(Item.info["medical_category"]).all()
                return medical
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_ammo():
        """
        ammo 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                ammo = s.query(Item).filter(Item.category == 'Ammo').order_by(cast(func.coalesce(Item.info["penetration_power"], "0"), Numeric)).all()
                return ammo
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_loot():
        """
        loot 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_loot_query())
                result = s.execute(query)
                loot = [dict(row) for row in result.mappings()]
                return loot
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_face_cover():
        """
        face cover 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                face_cover = s.query(Item).filter(Item.category == 'FaceCover').order_bycast(func.coalesce(Item.info["class_value"], "0"), Numeric).all()
            class_face_cover = []

            no_class_face_cover = []

            for cover in face_cover:
                if cover.info['class_value'] is None:
                    no_class_face_cover.append(cover)
                else:
                    class_face_cover.append(cover)

            result_face_cover = {
                "class_face_cover": [item.__dict__ for item in class_face_cover],
                "no_class_face_cover": [item.__dict__ for item in no_class_face_cover],
            }

            return result_face_cover
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_arm_band():
        """
        arm band 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                arm_band = s.query(Item).filter(Item.category == 'Armband').order_by(Item.name_en).all()
                return arm_band
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_glasses():
        """
        glasses 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_glasses_query())

                result = s.execute(query)
                glasses = [dict(row) for row in result.mappings()]

            class_glasses = []
            no_class_glasses = []

            for glass in glasses:
                if glass.get("class_value") == 0:
                    no_class_glasses.append(glass)
                else:
                    class_glasses.append(glass)

            result_glasses = {
                "class_glasses": class_glasses,
                "no_class_glasses": no_class_glasses,
            }

            return result_glasses
        except Exception as e:
            print("오류 발생:", e)
            return None
