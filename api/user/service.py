from api.user.user_req_models import AddUserReq
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from api.user.user_function import UserFunction

load_dotenv()


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            uuid_v5 = f"{os.getenv('UUID_NAME')}-{uuid.uuid5(uuid.NAMESPACE_DNS, addUserReq.email)}"
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                check_user = UserFunction._get_existing_user(s, addUserReq.email)
                if check_user:
                    UserFunction._handle_existing_user(s, check_user)
                else:
                    UserFunction._handle_new_user(s, addUserReq, uuid_v5)
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_user(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction._get_user_data(s, user_email)
                return user_data
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_nickname(new_nickname: str, user_email: str):
        """
        요건 적합 : return user
        30일 안지남 : return 2
        중복 : return 3
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)

                if UserFunction._is_nickname_change_allowed(user):
                    if UserFunction._is_nickname_duplicate(s, new_nickname):
                        return 3  # 중복
                    else:
                        UserFunction._update_nickname(s, user, new_nickname)
                        user_data = UserFunction._get_user_data(s, user_email)
                        return user_data
                else:
                    return 2  # 30일 안 되었음
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_icon(new_icon: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    user.icon = new_icon
                    s.commit()
                user_data = UserFunction._get_user_data(s, user_email)
                return user_data
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def user_delete(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    UserFunction._create_delete_user(s, user)
                    return True
                else:
                    return False
        except Exception as e:
            print("오류 발생:", e)
            return None
