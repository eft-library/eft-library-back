from api.user.user_res_models import User
from api.planner.planner_res_models import UserQuest
from api.user.user_req_models import AddUserReq
from datetime import datetime, timedelta, date
import pytz
from sqlalchemy import text
import re
from api.user.util import UserUtil


class UserFunction:
    @staticmethod
    def _get_existing_user(session, email: str) -> User:
        return session.query(User).filter(User.email == email).first()

    @staticmethod
    def _check_nickname_duplicate(session, nickname: str):
        return session.query(User).filter(User.nickname == nickname).first()

    @staticmethod
    def _handle_existing_user(session, user: User):
        today = date.today()
        tz = pytz.timezone("Asia/Seoul")
        start_of_today, end_of_today = UserFunction._get_start_and_end_of_day(tz, today)

        if user.attendance_time.tzinfo is None:
            user.attendance_time = tz.localize(user.attendance_time)

        if not (start_of_today <= user.attendance_time <= end_of_today):
            user.attendance_count += 1
            user.attendance_time = datetime.now(tz)
            session.commit()

    @staticmethod
    def _get_start_and_end_of_day(tz, today):
        start_of_today = tz.localize(datetime.combine(today, datetime.min.time()))
        end_of_today = tz.localize(datetime.combine(today, datetime.max.time()))
        return start_of_today, end_of_today

    @staticmethod
    def _create_delete_user(session, user: User):
        session.delete(user)
        session.commit()

    @staticmethod
    def _create_new_user(session, addUserReq: AddUserReq):
        new_user = User(
            id=addUserReq.id,
            name=addUserReq.name,
            email=addUserReq.email,
            is_admin=False,
            attendance_count=1,
            create_time=datetime.now(),
            attendance_time=datetime.now(),
        )
        session.add(new_user)
        UserFunction._create_user_related_entries(
            session,
            addUserReq.email,
        )
        session.commit()

    @staticmethod
    def delete_all_user_data(session):
        user_quest = text(UserUtil.delete_user_quest())
        user_hideout = text(UserUtil.delete_user_hideout())
        user_roadmap = text(UserUtil.delete_user_roadmap())
        user_progress_item = text(UserUtil.delete_user_progress_item())
        session.execute(user_quest)
        session.execute(user_hideout)
        session.execute(user_roadmap)
        session.execute(user_progress_item)
        return True

    @staticmethod
    def _create_user_related_entries(session, email: str):
        new_user_quest = UserQuest(
            user_email=email, quest_list=[], update_time=datetime.now()
        )
        session.add(new_user_quest)

    @staticmethod
    def _get_user_data(session, user_email: str):
        user_info_query = text(UserUtil.get_user_info_with_penalty())
        result = session.execute(user_info_query, {"user_email": user_email})
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def get_my_page_default(session, user_email: str):
        my_page_default_query = text(UserUtil.get_my_page_default())
        result = session.execute(my_page_default_query, {"user_email": user_email})
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def get_my_page_posts(session, user_email: str, limit: int, offset: int):
        my_page_posts_query = text(UserUtil.get_my_page_posts())
        my_page_posts_result = session.execute(
            my_page_posts_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        my_page_posts_total_query = text(UserUtil.get_my_page_posts_total())
        my_page_posts_total_result = session.execute(
            my_page_posts_total_query,
            {"user_email": user_email},
        )
        total = my_page_posts_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "posts": [dict(row) for row in my_page_posts_result.mappings()],
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def get_my_page_bookmarks(session, user_email: str, limit: int, offset: int):
        my_page_bookmarks_query = text(UserUtil.get_my_page_bookmarks())
        my_page_bookmarks_result = session.execute(
            my_page_bookmarks_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        my_page_bookmarks_total_query = text(UserUtil.get_my_page_bookmarks_total())
        my_page_bookmarks_total_result = session.execute(
            my_page_bookmarks_total_query,
            {"user_email": user_email},
        )
        total = my_page_bookmarks_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "bookmarks": [dict(row) for row in my_page_bookmarks_result.mappings()],
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def get_my_page_blocks(session, user_email: str, limit: int, offset: int):
        my_page_blocks_query = text(UserUtil.get_my_page_blocks())
        my_page_blocks_result = session.execute(
            my_page_blocks_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        my_page_blocks_total_query = text(UserUtil.get_my_page_blocks_total())
        my_page_blocks_total_result = session.execute(
            my_page_blocks_total_query,
            {"user_email": user_email},
        )
        total = my_page_blocks_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "blocks": [dict(row) for row in my_page_blocks_result.mappings()],
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def get_my_page_follow(session, user_email: str, limit: int, offset: int):
        my_page_follow_query = text(UserUtil.get_my_page_follow())
        my_page_follow_result = session.execute(
            my_page_follow_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        my_page_follow_total_query = text(UserUtil.get_my_page_follow_total())
        my_page_follow_total_result = session.execute(
            my_page_follow_total_query,
            {"user_email": user_email},
        )
        total = my_page_follow_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "follow": [dict(row) for row in my_page_follow_result.mappings()],
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def get_my_page_notification(session, user_email: str, limit: int, offset: int):
        # 1) 알림 조회
        my_page_notification_query = text(UserUtil.get_my_page_notification())
        my_page_notification_result = session.execute(
            my_page_notification_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        notifications = [dict(row) for row in my_page_notification_result.mappings()]

        # 2) 전체 카운트 조회
        my_page_notification_total_query = text(
            UserUtil.get_my_page_notification_total()
        )
        my_page_notification_total_result = session.execute(
            my_page_notification_total_query,
            {"user_email": user_email},
        )
        total = my_page_notification_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        # 3) 조회된 알림 읽음 처리 (is_read = TRUE)
        if notifications:  # 조회된 알림이 있을 경우만 업데이트
            ids = [n["id"] for n in notifications if not n.get("is_read", False)]
            if ids:
                mark_read_query = text(UserUtil.update_my_page_notification())
                session.execute(mark_read_query, {"ids": ids})
                session.commit()  # 커밋 필요 (트랜잭션 반영)

        return {
            "notifications": notifications,
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def get_my_page_comments(session, user_email: str, limit: int, offset: int):
        my_page_comments_query = text(UserUtil.get_my_page_comments())
        my_page_comments_result = session.execute(
            my_page_comments_query,
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        my_page_comments_total_query = text(UserUtil.get_my_page_comments_total())
        my_page_comments_total_result = session.execute(
            my_page_comments_total_query,
            {"user_email": user_email},
        )
        total = my_page_comments_total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "comments": [dict(row) for row in my_page_comments_result.mappings()],
            "total_count": total,
            "max_page_count": max_page_count,
        }

    @staticmethod
    def calculate_end_time(duration_value: str):
        """
        duration_value: "1day", "3days", "permanent" 등
        """
        now = datetime.now()

        if duration_value == "permanent":
            return None  # or datetime(9999, 12, 31, 23, 59, 59) 등

        # 숫자만 추출해서 int로 변환
        days = int("".join(filter(str.isdigit, duration_value)))

        # ban 종료일(자정)
        # 현재 날짜 + days => 그 날짜의 00:00:00
        target_date = (now + timedelta(days=days)).date()
        end_time = datetime.combine(target_date, datetime.min.time())

        return end_time

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
