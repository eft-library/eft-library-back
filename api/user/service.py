from datetime import datetime, timedelta, timezone
import json
import logging

from database import Database

from api.user.user_function import UserFunction
from api.user.user_req_models import AddUserReq, ReqUserBlock, ReqUserPenalty, ReqUserReport
from api.user.user_res_models import UserBlock, UserPenalty, UserReport
from util.kafka_producer import produce_notification
from util.http_exceptions import HttpError

logger = logging.getLogger("api.user")


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            with Database.SessionLocal() as s:
                UserFunction._upsert_user_info(s, addUserReq)
                return True
        except Exception as e:
            logger.error(
                f"add_new_user_v3: {addUserReq.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_user(user_email: str):
        try:
            with Database.SessionLocal() as s:
                UserFunction._update_attendance_if_needed(s, user_email)
                return UserFunction._get_user_data(s, user_email)
        except Exception as e:
            logger.error(f"get_user_v3 error: {e}", exc_info=True)
            raise HttpError.USER_LOOKUP_UNAVAILABLE.exception() from None

    @staticmethod
    def user_delete(user_email: str):
        try:
            with Database.SessionLocal() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if user:
                    UserFunction._create_delete_user(s, user)
                    UserFunction.delete_all_user_data(s, user_email)
                    s.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"user_delete_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def update_nickname(nickname: str, user_email: str):
        try:
            valid, message = UserFunction._validate_nickname_rules(nickname)
            if not valid:
                return {"success": False, **message}

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

            with Database.SessionLocal() as s:
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
                return {
                    "success": False,
                    "ko": "사용자를 찾을 수 없습니다.",
                    "jp": "ユーザーが見つかりません。",
                    "en": "User not found.",
                }
        except Exception as e:
            logger.error(f"update_nickname_v3: {nickname}, error: {e}", exc_info=True)
            return {
                "success": False,
                "ko": "서버 오류 발생",
                "jp": "サーバーエラーが発生しました。",
                "en": "A server error has occurred.",
            }

    @staticmethod
    def check_nickname_duplicate(nickname: str):
        try:
            with Database.SessionLocal() as s:
                user = UserFunction._check_nickname_duplicate(s, nickname)
                return {"result": 1 if user else 0}
        except Exception as e:
            logger.error(
                f"check_nickname_duplicate_v3: {nickname}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def check_last_update_nickname(user_email: str):
        try:
            with Database.SessionLocal() as s:
                user = UserFunction._get_existing_user(s, user_email)
                if not user:
                    return {"result": 0}
                if user.last_update_nickname:
                    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
                    if user.nickname is None:
                        return {"result": 1}
                    if user.last_update_nickname > thirty_days_ago:
                        return {"result": 0}
                return {"result": 1}
        except Exception as e:
            logger.error(f"check_last_update_nickname_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def report_user(request_info: ReqUserReport, user_email: str):
        try:
            with Database.SessionLocal() as s:
                s.add(
                    UserReport(
                        request_email=user_email,
                        target_email=request_info.reported_email,
                        reason_type=request_info.reason_type,
                        reason=request_info.reason,
                        request_time=datetime.now(),
                    )
                )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"report_user_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def block_user(request_info: ReqUserBlock, user_email: str):
        try:
            with Database.SessionLocal() as s:
                s.add(
                    UserBlock(
                        request_email=user_email,
                        target_email=request_info.blocked_email,
                        reason=request_info.reason,
                        create_time=datetime.now(),
                    )
                )
                s.commit()
                update_data = (
                    s.query(UserBlock)
                    .filter(UserBlock.request_email == user_email)
                    .all()
                )
                return {"result": update_data}
        except Exception as e:
            logger.error(
                f"block_user_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def unblock_user(request_info: ReqUserBlock, user_email: str):
        try:
            with Database.SessionLocal() as s:
                block_info = (
                    s.query(UserBlock)
                    .filter(
                        UserBlock.request_email == user_email,
                        UserBlock.target_email == request_info.blocked_email,
                    )
                    .first()
                )
                if block_info:
                    s.delete(block_info)
                    s.commit()
                update_data = (
                    s.query(UserBlock)
                    .filter(UserBlock.request_email == user_email)
                    .all()
                )
                return {"result": update_data}
        except Exception as e:
            logger.error(
                f"unblock_user_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def penalty_user(request_info: ReqUserPenalty):
        try:
            with Database.SessionLocal() as s:
                end_time = UserFunction.calculate_end_time(request_info.penalty)
                start_time = datetime.now()
                s.add(
                    UserPenalty(
                        email=request_info.user_email,
                        reason=request_info.reason,
                        start_time=start_time,
                        end_time=end_time,
                    )
                )
                s.commit()
                produce_notification(
                    json.dumps(
                        {
                            "user_email": request_info.user_email,
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat() if end_time else None,
                            "noti_type": "penalty_user",
                        }
                    )
                )
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"penalty_user_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _get_my_page_paged(user_email: str, page_num: int, fn, label: str):
        try:
            limit, offset = 10, (page_num - 1) * 10
            with Database.SessionLocal() as s:
                return fn(s, user_email, limit, offset)
        except Exception as e:
            logger.error(f"get_my_page_{label}_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_my_page_default(user_email: str):
        try:
            with Database.SessionLocal() as s:
                return UserFunction.get_my_page_default(s, user_email)
        except Exception as e:
            logger.error(f"get_my_page_default_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_my_page_info(user_email: str):
        return UserService.get_user(user_email)

    @staticmethod
    def get_my_page_posts(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_posts, "posts"
        )

    @staticmethod
    def get_my_page_comments(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_comments, "comments"
        )

    @staticmethod
    def get_my_page_bookmarks(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_bookmarks, "bookmarks"
        )

    @staticmethod
    def get_my_page_blocks(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_blocks, "blocks"
        )

    @staticmethod
    def get_my_page_follow(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_follow, "follow"
        )

    @staticmethod
    def get_my_page_notification(user_email: str, page_num: int):
        return UserService._get_my_page_paged(
            user_email, page_num, UserFunction.get_my_page_notification, "notification"
        )
