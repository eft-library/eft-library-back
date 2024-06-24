from api.item.models import (
    Headset,
    HeadWear,
    ArmorVest,
    Rig,
    Backpack,
    Container,
    Key,
    FoodDrink,
    Medical,
    Ammo,
)
from database import DataBaseConnector
from sqlalchemy import desc


class ItemService:
    @staticmethod
    def get_all_headset():
        """
        headset 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headset = s.query(Headset).order_by(Headset.name).all()
                return headset
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_head_wear():
        """
        head_wear 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                head_wear = s.query(HeadWear).order_by(HeadWear.class_value).all()

            class_head_wear = []

            no_class_head_wear = []

            for wear in head_wear:
                if wear.class_value is None:
                    no_class_head_wear.append(wear)
                else:
                    class_head_wear.append(wear)

            result_head_wear = {
                "class_head_wear": [item.__dict__ for item in class_head_wear],
                "no_class_head_wear": [item.__dict__ for item in no_class_head_wear],
            }

            return result_head_wear
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
                armor_vest = s.query(ArmorVest).order_by(ArmorVest.class_value).all()
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
                backpack = s.query(Backpack).order_by(Backpack.capacity).all()
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
                container = s.query(Container).order_by(Container.capacity).all()
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
                key = s.query(Key).order_by(Key.name).all()
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
                rig = s.query(Rig).order_by(Rig.class_value, Rig.capacity).all()

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
    def get_all_food_drink():
        """
        food drink 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                food_drink = (
                    s.query(FoodDrink)
                    .order_by(
                        desc(FoodDrink.category), FoodDrink.energy, FoodDrink.hydration
                    )
                    .all()
                )
                return food_drink
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
                medical = s.query(Medical).order_by(Medical.category).all()
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
                ammo = s.query(Ammo).order_by(Ammo.armor_damage).all()
                return ammo
        except Exception as e:
            print("오류 발생:", e)
            return None
