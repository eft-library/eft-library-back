from datetime import datetime, timedelta, timezone
import json
import logging

from database import V3Database

from api.user.user_function import UserFunctionV3
from api.user.user_req_models import AddUserReq, ReqUserBlock, ReqUserPenalty, ReqUserReport
from api.user.user_res_models import UserBlockV3, UserPenaltyV3, UserReportV3
from util.kafka_producer import produce_notification

logger = logging.getLogger("api.user")


class UserServiceV3:
    @staticmethod
    def add_new_user_v3(addUserReq: AddUserReq):
        try:
            with V3Database.SessionLocal() as s:
                UserFunctionV3._upsert_user_info_v3(s, addUserReq)
                return True
        except Exception as e:
            logger.error(
                f"add_new_user_v3: {addUserReq.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_user_v3(user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                UserFunctionV3._update_attendance_if_needed_v3(s, user_email)
                return UserFunctionV3._get_user_data_v3(s, user_email)
        except Exception as e:
            logger.error(f"get_user_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def user_delete_v3(user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                user = UserFunctionV3._get_existing_user_v3(s, user_email)
                if user:
                    UserFunctionV3._create_delete_user_v3(s, user)
                    UserFunctionV3.delete_all_user_data_v3(s, user_email)
                    s.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"user_delete_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def update_nickname_v3(nickname: str, user_email: str):
        try:
            valid, message = UserFunctionV3._validate_nickname_rules_v3(nickname)
            if not valid:
                return {"success": False, **message}

            last_check = UserServiceV3.check_last_update_nickname_v3(user_email)
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

            duplicate_check = UserServiceV3.check_nickname_duplicate_v3(nickname)
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

            with V3Database.SessionLocal() as s:
                user = UserFunctionV3._get_existing_user_v3(s, user_email)
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
    def check_nickname_duplicate_v3(nickname: str):
        try:
            with V3Database.SessionLocal() as s:
                user = UserFunctionV3._check_nickname_duplicate_v3(s, nickname)
                return {"result": 1 if user else 0}
        except Exception as e:
            logger.error(
                f"check_nickname_duplicate_v3: {nickname}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def check_last_update_nickname_v3(user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                user = UserFunctionV3._get_existing_user_v3(s, user_email)
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
    def report_user_v3(request_info: ReqUserReport, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                s.add(
                    UserReportV3(
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
    def block_user_v3(request_info: ReqUserBlock, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                s.add(
                    UserBlockV3(
                        request_email=user_email,
                        target_email=request_info.blocked_email,
                        reason=request_info.reason,
                        create_time=datetime.now(),
                    )
                )
                s.commit()
                update_data = (
                    s.query(UserBlockV3)
                    .filter(UserBlockV3.request_email == user_email)
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
    def unblock_user_v3(request_info: ReqUserBlock, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                block_info = (
                    s.query(UserBlockV3)
                    .filter(
                        UserBlockV3.request_email == user_email,
                        UserBlockV3.target_email == request_info.blocked_email,
                    )
                    .first()
                )
                if block_info:
                    s.delete(block_info)
                    s.commit()
                update_data = (
                    s.query(UserBlockV3)
                    .filter(UserBlockV3.request_email == user_email)
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
    def penalty_user_v3(request_info: ReqUserPenalty):
        try:
            with V3Database.SessionLocal() as s:
                end_time = UserFunctionV3.calculate_end_time_v3(request_info.penalty)
                start_time = datetime.now()
                s.add(
                    UserPenaltyV3(
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
    def _get_my_page_paged_v3(user_email: str, page_num: int, fn, label: str):
        try:
            limit, offset = 10, (page_num - 1) * 10
            with V3Database.SessionLocal() as s:
                return fn(s, user_email, limit, offset)
        except Exception as e:
            logger.error(f"get_my_page_{label}_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_my_page_default_v3(user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                return UserFunctionV3.get_my_page_default_v3(s, user_email)
        except Exception as e:
            logger.error(f"get_my_page_default_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_my_page_info_v3(user_email: str):
        return UserServiceV3.get_user_v3(user_email)

    @staticmethod
    def get_my_page_posts_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_posts_v3, "posts"
        )

    @staticmethod
    def get_my_page_comments_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_comments_v3, "comments"
        )

    @staticmethod
    def get_my_page_bookmarks_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_bookmarks_v3, "bookmarks"
        )

    @staticmethod
    def get_my_page_blocks_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_blocks_v3, "blocks"
        )

    @staticmethod
    def get_my_page_follow_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_follow_v3, "follow"
        )

    @staticmethod
    def get_my_page_notification_v3(user_email: str, page_num: int):
        return UserServiceV3._get_my_page_paged_v3(
            user_email, page_num, UserFunctionV3.get_my_page_notification_v3, "notification"
        )
