from datetime import datetime, timezone, timedelta
import re
from api.user.user_req_models import AddUserReq, ReqUserReport, ReqUserBlock
from database import DataBaseConnector
from api.user.user_function import UserFunction
from api.user.user_res_models import UserReport, UserBlock


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
            return False, {
                "ko": "닉네임은 2~12자 사이여야 합니다.",
                "jp": "ニックネームは2〜12文字である必要があります。",
                "en": "Nickname must be between 2 and 12 characters.",
            }

        # 2. 허용 문자 체크 (한글, 영문, 숫자, _, -)
        if not re.match(r"^[가-힣a-zA-Z0-9_-]+$", nickname):
            return False, {
                "ko": "닉네임에는 한글, 영문, 숫자, _, -만 사용할 수 있습니다.",
                "jp": "ニックネームには韓国語、英語、数字、_, -のみ使用できます。",
                "en": "Nickname can only contain Korean, English letters, numbers, _, -.",
            }

        # 3. 금지 단어 체크
        lower_nick = nickname.lower()
        if any(word.lower() in lower_nick for word in forbidden_words):
            return False, {
                "ko": "사용할 수 없는 단어가 포함되어 있습니다.",
                "jp": "使用できない単語が含まれています。",
                "en": "Nickname contains forbidden words.",
            }

        return True, {
            "ko": "사용 가능한 닉네임입니다.",
            "jp": "使用可能なニックネームです。",
            "en": "Nickname is available.",
        }

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
                return {
                    "success": False,
                    "ko": message["ko"],
                    "jp": message["jp"],
                    "en": message["en"],
                }

            # 2️⃣ 마지막 업데이트 30일 체크
            last_check = UserService.check_last_update_nickname(user_email)
            if last_check is None:
                return {
                    "success": False,
                    "ko": "유저 정보를 확인하는 중 오류 발생",
                    "jp": "ユーザー情報の確認中にエラーが発生しました。",
                    "en": "An error occurred while checking user information.",
                }
            if last_check.get("result") == 0:
                return {
                    "success": False,
                    "ko": "닉네임은 30일에 1회만 변경할 수 있습니다.",
                    "jp": "ニックネームは30日に1回しか変更できません。",
                    "en": "Nickname can only be changed once every 30 days.",
                }

            # 3️⃣ 중복 체크
            duplicate_check = UserService.check_nickname_duplicate(nickname)
            if duplicate_check is None:
                return {
                    "success": False,
                    "ko": "닉네임 중복 확인 중 오류 발생",
                    "jp": "ニックネームの重複確認中にエラーが発生しました。",
                    "en": "An error occurred while checking nickname duplication.",
                }
            if duplicate_check.get("result") == 1:
                return {
                    "success": False,
                    "ko": "이미 사용 중인 닉네임입니다.",
                    "jp": "すでに使用されているニックネームです。",
                    "en": "This nickname is already in use.",
                }

            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    user.nickname = nickname
                    user.last_update_nickname = datetime.now()
                    s.commit()
                    return {
                        "success": True,
                        "ko": "닉네임이 성공적으로 변경되었습니다.",
                        "jp": "ニックネームが正常に変更されました。",
                        "en": "Nickname has been successfully updated.",
                    }
                else:
                    return {
                        "success": False,
                        "ko": "사용자를 찾을 수 없습니다.",
                        "jp": "ユーザーが見つかりません。",
                        "en": "User not found.",
                    }

        except Exception as e:
            print("오류 발생:", e)
            return {
                "success": False,
                "ko": "서버 오류 발생",
                "jp": "サーバーエラーが発生しました。",
                "en": "A server error has occurred.",
            }

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
                    # timezone-aware now
                    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
                    if user.nickname is None:
                        return {"result": 1}
                    if user.last_update_nickname > thirty_days_ago:
                        # 30일 안 지남 → 업데이트 불가
                        return {"result": 0}

                # 30일 이상 지났거나 처음 업데이트
                return {"result": 1}

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def report_user(request_info: ReqUserReport, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_post_report = UserReport(
                    reporter_email=user_email,
                    reported_email=request_info.reported_email,
                    reason_type=request_info.reason_type,
                    reason=request_info.reason,
                    create_time=datetime.now(),
                )
                s.add(new_post_report)
                s.commit()

                return {"result": 1}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def block_user(request_info: ReqUserBlock, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_block = UserReport(
                    blocker_email=user_email,
                    blocked_email=request_info.blocked_email,
                    reason=request_info.reason,
                    create_time=datetime.now(),
                )
                s.add(new_block)
                s.commit()

                return {"result": 1}
        except Exception as e:
            print("오류 발생:", e)
            return None
