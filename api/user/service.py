from datetime import datetime, timezone, timedelta
from api.user.user_req_models import (
    AddUserReq,
    ReqUserReport,
    ReqUserBlock,
    ReqUserPenalty,
)
from database import DataBaseConnector
from api.user.user_function import UserFunction
from api.user.user_res_models import UserReport, UserBlock, UserPenalty
from util.kafka_producer import produce_notification
import json
import logging

logger = logging.getLogger("api.user")


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
            logger.error(
                f"add_new_user: {addUserReq.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_user(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction._get_user_data(s, user_email)
                return user_data
        except Exception as e:
            logger.error(
                f"get_user error: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"user_delete error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def update_nickname(nickname: str, user_email: str):
        try:
            # 닉네임 규칙 체크
            valid, message = UserFunction._validate_nickname_rules(nickname)
            if not valid:
                return {
                    "success": False,
                    "ko": message["ko"],
                    "jp": message["jp"],
                    "en": message["en"],
                }

            # 마지막 업데이트 30일 체크
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

            # 중복 체크
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
            logger.error(
                f"update_nickname: {nickname}, error: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"check_nickname_duplicate: {nickname}, error: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"check_last_update_nickname error: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"report_user: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def block_user(request_info: ReqUserBlock, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_block = UserBlock(
                    blocker_email=user_email,
                    blocked_email=request_info.blocked_email,
                    reason=request_info.reason,
                    create_time=datetime.now(),
                )
                s.add(new_block)
                s.commit()

                update_data = (
                    s.query(UserBlock)
                    .filter(UserBlock.blocker_email == user_email)
                    .all()
                )

                return {"result": update_data}
        except Exception as e:
            logger.error(
                f"block_user: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def unblock_user(request_info: ReqUserBlock, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                block_info = (
                    s.query(UserBlock)
                    .filter(
                        UserBlock.blocker_email == user_email,
                        UserBlock.blocked_email == request_info.blocked_email,
                    )
                    .first()
                )
                if block_info:
                    s.delete(block_info)
                    s.commit()

                update_data = (
                    s.query(UserBlock)
                    .filter(UserBlock.blocker_email == user_email)
                    .all()
                )

                return {"result": update_data}
        except Exception as e:
            logger.error(
                f"unblock_user: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def penalty_user(request_info: ReqUserPenalty):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                end_time = UserFunction.calculate_end_time(request_info.penalty)
                start_time = datetime.now()
                new_block = UserPenalty(
                    user_email=request_info.user_email,
                    reason=request_info.reason,
                    start_time=start_time,
                    end_time=end_time,
                )
                s.add(new_block)
                s.commit()

                kafka_message = {
                    "user_email": request_info.user_email,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "noti_type": "penalty_user",
                }
                json_str = json.dumps(kafka_message)
                produce_notification(json_str)

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"penalty_user: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    # 사용자 기본 정보
    @staticmethod
    def get_my_page_default(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_default(s, user_email)
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_default error: {e}",
                exc_info=True,
            )
            return None

    # 사용자 정보 페이지
    @staticmethod
    def get_my_page_info(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction._get_user_data(s, user_email)
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_info error: {e}",
                exc_info=True,
            )
            return None

    # 작성글 목록
    @staticmethod
    def get_my_page_posts(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_posts(s, user_email, limit, offset)
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_posts error: {e}",
                exc_info=True,
            )
            return None

    # 작성 댓글 목록
    @staticmethod
    def get_my_page_comments(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_comments(
                    s, user_email, limit, offset
                )
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_comments error: {e}",
                exc_info=True,
            )
            return None

    # 북마크 목록
    @staticmethod
    def get_my_page_bookmarks(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_bookmarks(
                    s, user_email, limit, offset
                )
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_bookmarks error: {e}",
                exc_info=True,
            )
            return None

    # 차단한 사람 목록
    @staticmethod
    def get_my_page_blocks(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_blocks(
                    s, user_email, limit, offset
                )
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_blocks error: {e}",
                exc_info=True,
            )
            return None

    # 차단한 사람 목록
    @staticmethod
    def get_my_page_follow(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_follow(
                    s, user_email, limit, offset
                )
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_follow error: {e}",
                exc_info=True,
            )
            return None

    # 차단한 사람 목록
    @staticmethod
    def get_my_page_notification(user_email: str, page_num: int):
        try:
            limit, offset = 10, (page_num - 1) * 10
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserFunction.get_my_page_notification(
                    s, user_email, limit, offset
                )
                return user_data
        except Exception as e:
            logger.error(
                f"get_my_page_notification error: {e}",
                exc_info=True,
            )
            return None
