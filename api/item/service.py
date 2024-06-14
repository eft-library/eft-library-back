from api.item.models import Headset, HeadWear, ArmorVest, Rig, Backpack, Container, Key
from database import DataBaseConnector


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
