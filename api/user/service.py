from datetime import datetime, timedelta

from api.user.user_req_models import AddUserReq
from database import DataBaseConnector
from api.user.user_function import UserFunction


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                check_user = UserFunction._get_existing_user(s, addUserReq.email)
                if check_user:
                    UserFunction._handle_existing_user(s, check_user)
                else:
                    UserFunction._create_new_user(s, addUserReq)
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

    @staticmethod
    def update_nickname(nickname: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    user.nickname = nickname
                    user.last_update_nickname = datetime.now()
                    s.commit()
                    return True
                else:
                    return False
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def check_nickname_duplicate(nickname: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._check_nickname_duplicate(s, nickname)
                if user:
                    return {"result": 1}
                else:
                    return {"result": 0}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def check_last_update_nickname(user_email: str):
        """
        닉네임 마지막 업데이트가 30일 이내인지 체크.
        - 30일 안 지났으면 False 반환 (업데이트 불가)
        - 30일 이상 지났거나 유저 존재하지 않으면 True 반환 (업데이트 가능)
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if not user:
                    return {"result": 0}  # 유저 존재하지 않음

                # 30일 이전 체크
                if user.last_update_nickname:
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    if user.last_update_nickname > thirty_days_ago:
                        # 30일 안 지남 → 업데이트 불가
                        return {"result": 0}

                # 30일 이상 지났거나 처음 업데이트
                return {"result": 1}

        except Exception as e:
            print("오류 발생:", e)
            return None
