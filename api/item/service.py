from api.item.models import Item
from api.item.util import ItemUtil
from database import DataBaseConnector
from sqlalchemy import text, cast, Numeric


class ItemService:
    @staticmethod
    def get_item_detail(item_url: str):
        """
        item 상세 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_item_detail_query())
                param = {"url_mapping": item_url}
                result = s.execute(query, param)
                item = result.mappings().first()
                return item
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_rig_list():
        """
        rig 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_rig_query())
                result = s.execute(query)
                rig = [dict(row) for row in result.mappings()]

            class_rig = []
            no_class_rig = []

            for item in rig:
                if item["info"]["class_value"] is None:
                    no_class_rig.append(item)
                else:
                    class_rig.append(item)

            result_rig = {
                "class_rig": class_rig,
                "no_class_rig": no_class_rig,
            }

            return result_rig
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_glasses_list():
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

            for item in glasses:
                if item["info"]["class_value"] == 0:
                    no_class_glasses.append(item)
                else:
                    class_glasses.append(item)

            result_glasses = {
                "class_glasses": class_glasses,
                "no_class_glasses": no_class_glasses,
            }

            return result_glasses
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_face_cover_list():
        """
        face cover 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                query = text(ItemUtil.get_face_cover_query())
                result = s.execute(query)
                face_cover = [dict(row) for row in result.mappings()]

            class_face_cover = []

            no_class_face_cover = []

            for item in face_cover:
                if item["info"]["class_value"] is None:
                    no_class_face_cover.append(item)
                else:
                    class_face_cover.append(item)

            result_face_cover = {
                "class_face_cover": class_face_cover,
                "no_class_face_cover": no_class_face_cover,
            }

            return result_face_cover
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_medical_list():
        """
        medical 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                medical = (
                    s.query(Item)
                    .filter(Item.category == "Medical")
                    .order_by(Item.info["medical_category"])
                    .all()
                )
                result = {}

                for item in medical:
                    # 카테고리 키에서 공백 제거하고 소문자로 변환
                    raw_category = item.info.get("medical_category", "Unknown")
                    category = raw_category.replace(" ", "")

                    if category not in result:
                        result[category] = []
                    result[category].append(item)

                return result
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_container_list():
        """
        container 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                container = (
                    s.query(Item)
                    .filter(Item.category == "Container")
                    .order_by(cast(Item.info["capacity"], Numeric))
                    .all()
                )
                return container
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_arm_band_list():
        """
        arm band 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                arm_band = s.query(Item).filter(Item.category == "Armband").all()
                return arm_band
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_loot_list():
        """
        loot 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                loot = s.query(Item).filter(Item.category == "Loot").all()
                return loot
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_ammo_list():
        """
        ammo 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                ammo = (
                    s.query(Item)
                    .filter(Item.category == "Ammo")
                    .order_by(cast(Item.info["penetration_power"], Numeric))
                    .all()
                )
                return ammo
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_provisions_list():
        """
        provisions 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                provisions = s.query(Item).filter(Item.category == "Provisions").all()
                return provisions
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_key_list():
        """
        key 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                key = s.query(Item).filter(Item.category == "Key").all()
                return key
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_armor_vest_list():
        """
        armor vest 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_armor_vest_query())
                result = s.execute(query)
                armor_vest = [dict(row) for row in result.mappings()]
                return armor_vest
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_backpack_list():
        """
        backpack 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                backpack = (
                    s.query(Item)
                    .filter(Item.category == "Backpack")
                    .order_by(cast(Item.info["capacity"], Numeric))
                    .all()
                )
                return backpack
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_headset_list():
        """
        headset 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headset = s.query(Item).filter(Item.category == "Headset").all()
                return headset
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_weapon_list():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                weapon_list = {
                    "gun": s.query(Item).filter(Item.category == "Gun").all(),
                    "knife": s.query(Item).filter(Item.category == "Knife").all(),
                    "throwable": s.query(Item)
                    .filter(Item.category == "Throwable")
                    .all(),
                }
            return weapon_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_headwear_list():
        """
        headwear 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(ItemUtil.get_head_wear_query())
                result = s.execute(query)
                headwear = [dict(row) for row in result.mappings()]

            class_headwear = []

            no_class_headwear = []

            for item in headwear:
                if item["info"]["class_value"] is None:
                    no_class_headwear.append(item)
                else:
                    class_headwear.append(item)

            result_headwear = {
                "class_headwear": class_headwear,
                "no_class_headwear": no_class_headwear,
            }

            return result_headwear
        except Exception as e:
            print("오류 발생:", e)
            return None
