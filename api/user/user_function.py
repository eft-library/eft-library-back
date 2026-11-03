import re
from datetime import date, datetime, timedelta, timezone

import pytz
from sqlalchemy import case, func, or_, text, update
from sqlalchemy.dialects.postgresql import insert

from api.user.user_req_models import AddUserReq
from api.user.user_res_models import User
from api.user.util import PlatformUserUtil


class UserFunction:
    @staticmethod
    def _get_existing_user(session, email: str):
        return session.query(User).filter(User.email == email).first()

    @staticmethod
    def _check_nickname_duplicate(session, nickname: str):
        return session.query(User).filter(User.nickname == nickname).first()

    @staticmethod
    def _get_start_and_end_of_day(tz, today):
        start_of_today = tz.localize(datetime.combine(today, datetime.min.time()))
        end_of_today = tz.localize(datetime.combine(today, datetime.max.time()))
        return start_of_today, end_of_today

    @staticmethod
    def _handle_existing_user(session, user: User):
        today = date.today()
        tz = pytz.timezone("Asia/Seoul")
        start_of_today, end_of_today = UserFunction._get_start_and_end_of_day(
            tz, today
        )
        if user.attendance_time.tzinfo is None:
            user.attendance_time = tz.localize(user.attendance_time)
        if not (start_of_today <= user.attendance_time <= end_of_today):
            user.attendance_count += 1
            user.attendance_time = datetime.now(tz)
            session.commit()

    @staticmethod
    def _create_new_user(session, addUserReq: AddUserReq):
        session.add(
            User(
                name=addUserReq.name,
                email=addUserReq.email,
                is_admin=False,
                attendance_count=1,
                create_time=datetime.now(),
                attendance_time=datetime.now(),
            )
        )
        session.commit()

    @staticmethod
    def _upsert_user_info(session, addUserReq: AddUserReq):
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        start_of_today, end_of_today = UserFunction._get_start_and_end_of_day(
            tz, now.date()
        )

        stmt = insert(User).values(
            email=addUserReq.email,
            name=addUserReq.name,
            is_admin=False,
            attendance_count=1,
            attendance_time=now,
            create_time=now,
        )
        should_update_attendance = or_(
            User.attendance_time.is_(None),
            User.attendance_time < start_of_today,
            User.attendance_time > end_of_today,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.email],
            set_={
                "name": stmt.excluded.name,
                "attendance_count": case(
                    (
                        should_update_attendance,
                        func.coalesce(User.attendance_count, 0) + 1,
                    ),
                    else_=User.attendance_count,
                ),
                "attendance_time": case(
                    (should_update_attendance, now),
                    else_=User.attendance_time,
                ),
            },
        )
        session.execute(stmt)
        session.commit()

    @staticmethod
    def _update_attendance_if_needed(session, user_email: str):
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        start_of_today, end_of_today = UserFunction._get_start_and_end_of_day(
            tz, now.date()
        )
        should_update_attendance = or_(
            User.attendance_time.is_(None),
            User.attendance_time < start_of_today,
            User.attendance_time > end_of_today,
        )

        stmt = (
            update(User)
            .where(User.email == user_email, should_update_attendance)
            .values(
                attendance_count=func.coalesce(User.attendance_count, 0) + 1,
                attendance_time=now,
            )
        )
        session.execute(stmt)
        session.commit()

    @staticmethod
    def _create_delete_user(session, user: User):
        session.delete(user)

    @staticmethod
    def delete_all_user_data(session, email: str):
        param = {"email": email}
        session.execute(text(PlatformUserUtil.delete_user_roadmap()), param)
        return True

    @staticmethod
    def _get_user_data(session, user_email: str):
        result = session.execute(
            text(PlatformUserUtil.get_user_info_with_penalty()),
            {"user_email": user_email},
        )
        row = result.mappings().first()
        return dict(row) if row is not None else None

    @staticmethod
    def get_my_page_default(session, user_email: str):
        result = session.execute(
            text(PlatformUserUtil.get_my_page_default()),
            {"user_email": user_email},
        )
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def _get_paged_user_data(
        session, data_sql: str, count_sql: str, result_key: str, user_email: str, limit: int, offset: int
    ):
        data = session.execute(
            text(data_sql),
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        total = session.execute(text(count_sql), {"user_email": user_email}).scalar()
        return {
            result_key: [dict(row) for row in data.mappings()],
            "total_count": total,
            "max_page_count": (total + limit - 1) // limit,
        }

    @staticmethod
    def get_my_page_posts(session, user_email: str, limit: int, offset: int):
        return UserFunction._get_paged_user_data(
            session,
            PlatformUserUtil.get_my_page_posts(),
            PlatformUserUtil.get_my_page_posts_total(),
            "posts",
            user_email,
            limit,
            offset,
        )

    @staticmethod
    def get_my_page_comments(session, user_email: str, limit: int, offset: int):
        return UserFunction._get_paged_user_data(
            session,
            PlatformUserUtil.get_my_page_comments(),
            PlatformUserUtil.get_my_page_comments_total(),
            "comments",
            user_email,
            limit,
            offset,
        )

    @staticmethod
    def get_my_page_bookmarks(session, user_email: str, limit: int, offset: int):
        return UserFunction._get_paged_user_data(
            session,
            PlatformUserUtil.get_my_page_bookmarks(),
            PlatformUserUtil.get_my_page_bookmarks_total(),
            "bookmarks",
            user_email,
            limit,
            offset,
        )

    @staticmethod
    def get_my_page_blocks(session, user_email: str, limit: int, offset: int):
        return UserFunction._get_paged_user_data(
            session,
            PlatformUserUtil.get_my_page_blocks(),
            PlatformUserUtil.get_my_page_blocks_total(),
            "blocks",
            user_email,
            limit,
            offset,
        )

    @staticmethod
    def get_my_page_follow(session, user_email: str, limit: int, offset: int):
        return UserFunction._get_paged_user_data(
            session,
            PlatformUserUtil.get_my_page_follow(),
            PlatformUserUtil.get_my_page_follow_total(),
            "follow",
            user_email,
            limit,
            offset,
        )

    @staticmethod
    def get_my_page_notification(session, user_email: str, limit: int, offset: int):
        result = session.execute(
            text(PlatformUserUtil.get_my_page_notification()),
            {"limit": limit, "offset": offset, "user_email": user_email},
        )
        notifications = [dict(row) for row in result.mappings()]
        total = session.execute(
            text(PlatformUserUtil.get_my_page_notification_total()),
            {"user_email": user_email},
        ).scalar()
        if notifications:
            ids = [n["id"] for n in notifications if not n.get("is_read", False)]
            if ids:
                session.execute(text(PlatformUserUtil.update_my_page_notification()), {"ids": ids})
                session.commit()
        return {
            "notifications": notifications,
            "total_count": total,
            "max_page_count": (total + limit - 1) // limit,
        }

    @staticmethod
    def calculate_end_time(duration_value: str):
        now = datetime.now()
        if duration_value == "permanent":
            return None
        days = int("".join(filter(str.isdigit, duration_value)))
        target_date = (now + timedelta(days=days)).date()
        return datetime.combine(target_date, datetime.min.time())

    @staticmethod
    def _validate_nickname_rules(nickname: str):
        forbidden_words = ["욕설1", "욕설2", "admin", "운영진", "관리자", "운영자", "시발", "개새끼"]
        if len(nickname) < 2 or len(nickname) > 12:
            return False, {
                "ko": "닉네임은 2~12자 사이여야 합니다.",
                "jp": "ニックネームは2〜12文字である必要があります。",
                "en": "Nickname must be between 2 and 12 characters.",
            }
        if not re.match(r"^[가-힣a-zA-Z0-9_-]+$", nickname):
            return False, {
                "ko": "닉네임에는 한글, 영문, 숫자, _, -만 사용할 수 있습니다.",
                "jp": "ニックネームには韓国語、英語、数字、_, -のみ使用できます。",
                "en": "Nickname can only contain Korean, English letters, numbers, _, -.",
            }
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
