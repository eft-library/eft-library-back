from datetime import datetime, timedelta
import re
from api.user.user_req_models import AddUserReq
from database import DataBaseConnector
from api.user.user_function import UserFunction


class UserService:
    @staticmethod
    def _validate_nickname_rules(nickname: str):
        forbidden_words = [
            "욕설1",
            "욕설2",
            "admin",
            "운영진",
            "관리자",
            "운영자",
            "시발",
            "개새끼",
        ]
        # 1. 길이 체크
        if len(nickname) < 2 or len(nickname) > 12:
            return False, "닉네임은 2~12자 사이여야 합니다."

        # 2. 허용 문자 체크 (한글, 영문, 숫자, _, -)
        if not re.match(r"^[가-힣a-zA-Z0-9_-]+$", nickname):
            return False, "닉네임에는 한글, 영문, 숫자, _, -만 사용할 수 있습니다."

        # 3. 금지 단어 체크
        lower_nick = nickname.lower()
        if any(word.lower() in lower_nick for word in forbidden_words):
            return False, "사용할 수 없는 단어가 포함되어 있습니다."

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
            # 1️⃣ 닉네임 규칙 체크
            valid, message = UserService._validate_nickname_rules(nickname)
            if not valid:
                return {"success": False, "message": message}

            # 2️⃣ 마지막 업데이트 30일 체크
            last_check = UserService.check_last_update_nickname(user_email)
            if last_check is None:
                return {
                    "success": False,
                    "message": "유저 정보를 확인하는 중 오류 발생",
                }
            if last_check.get("result") == 0:
                return {
                    "success": False,
                    "message": "닉네임은 30일에 1회만 변경할 수 있습니다.",
                }

            # 3️⃣ 중복 체크
            duplicate_check = UserService.check_nickname_duplicate(nickname)
            if duplicate_check is None:
                return {"success": False, "message": "닉네임 중복 확인 중 오류 발생"}
            if duplicate_check.get("result") == 1:
                return {"success": False, "message": "이미 사용 중인 닉네임입니다."}

            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    user.nickname = nickname
                    user.last_update_nickname = datetime.now()
                    s.commit()
                    return {
                        "success": True,
                        "message": "닉네임이 성공적으로 변경되었습니다.",
                    }
                else:
                    return {"success": False, "message": "사용자를 찾을 수 없습니다."}

        except Exception as e:
            print("오류 발생:", e)
            return {"success": False, "message": "서버 오류 발생"}

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
