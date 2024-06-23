from api.item.models import (
    Headset,
    HeadWear,
    ArmorVest,
    Rig,
    Backpack,
    Container,
    Key,
    FoodDrink,
    Medical,Ammo
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
            session = DataBaseConnector.create_session()
            headset = session.query(Headset).order_by(Headset.name).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            head_wear = session.query(HeadWear).order_by(HeadWear.class_value).all()
            session.close()

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
    def get_all_armo_vest():
        """
        armor vest 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            headset = session.query(ArmorVest).order_by(ArmorVest.class_value).all()
            session.close()
            return headset
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_backpack():
        """
        backpack 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            backpack = session.query(Backpack).order_by(Backpack.capacity).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            container = session.query(Container).order_by(Container.capacity).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            key = session.query(Key).order_by(Key.name).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            rig = session.query(Rig).order_by(Rig.class_value, Rig.capacity).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            food_drink = (
                session.query(FoodDrink)
                .order_by(
                    desc(FoodDrink.category), FoodDrink.energy, FoodDrink.hydration
                )
                .all()
            )
            session.close()
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
            session = DataBaseConnector.create_session()
            medical = session.query(Medical).order_by(Medical.category).all()
            session.close()
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
            session = DataBaseConnector.create_session()
            ammo = session.query(Ammo).order_by(Ammo.category).all()
            session.close()
            return ammo
        except Exception as e:
            print("오류 발생:", e)
            return None
