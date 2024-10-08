from sqlalchemy import text, desc

from api.user.user_res_models import (
    User,
    UserQuest,
    UserGrade,
    UserIcon,
    UserBan,
    UserDelete,
    UserPostStatistics,
)
from api.user.user_req_models import AddUserReq, BanUser
from api.comment.comment_res_models import Comments
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from api.user.util import UserUtil
import pytz

load_dotenv()


default_icon = "/tkl_user/icon/cat.png"


class UserFunction:
    @staticmethod
    def _get_existing_user(session, email: str) -> User:
        return session.query(User).filter(User.email == email).first()

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
            user.point += 10
            session.commit()

    @staticmethod
    def _get_start_and_end_of_day(tz, today):
        start_of_today = tz.localize(datetime.combine(today, datetime.min.time()))
        end_of_today = tz.localize(datetime.combine(today, datetime.max.time()))
        return start_of_today, end_of_today

    @staticmethod
    def _handle_new_user(session, addUserReq: AddUserReq, uuid_v5: str):
        is_delete_user = UserFunction._get_deleted_user(session, addUserReq.email)
        if is_delete_user:
            UserFunction._revoke_deleted_user(session, is_delete_user)
        else:
            UserFunction._create_new_user(session, addUserReq, uuid_v5)

    @staticmethod
    def _get_deleted_user(session, email: str) -> UserDelete:
        return session.query(UserDelete).filter(UserDelete.email == email).first()

    @staticmethod
    def _revoke_deleted_user(session, user_delete: UserDelete):
        revoked_user = User(
            id=user_delete.id,
            name=user_delete.name,
            email=user_delete.email,
            icon=user_delete.icon,
            nick_name=user_delete.nick_name,
            point=user_delete.point,
            grade=user_delete.grade,
            is_admin=user_delete.is_admin,
            attendance_count=user_delete.attendance_count,
            create_time=user_delete.create_time,
            attendance_time=user_delete.attendance_time,
            update_time=user_delete.update_time,
        )
        session.add(revoked_user)
        session.delete(user_delete)
        session.commit()

    @staticmethod
    def _create_delete_user(session, user: User):
        new_delete_user = UserDelete(
            id=user.id,
            name=user.name,
            email=user.email,
            icon=user.icon,
            nick_name=user.nick_name,
            point=user.point,
            grade=user.grade,
            is_admin=user.is_admin,
            attendance_count=user.attendance_count,
            create_time=user.create_time,
            update_time=user.update_time,
            attendance_time=user.attendance_time,
            delete_end_time=datetime.now() + timedelta(days=30),
        )
        session.add(new_delete_user)
        session.delete(user)
        session.commit()

    @staticmethod
    def _create_new_user(session, addUserReq: AddUserReq, uuid_v5: str):
        new_user = User(
            id=addUserReq.id,
            name=addUserReq.name,
            email=addUserReq.email,
            icon=default_icon,
            nick_name=uuid_v5[:10],
            point=10,
            grade=1,
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
    def _create_user_related_entries(session, email: str):
        new_user_quest = UserQuest(
            user_email=email,
            quest_id=[],
        )
        session.add(new_user_quest)
        new_icon_list = UserIcon(
            user_email=email,
            icon_list=[default_icon],
        )
        session.add(new_icon_list)

    @staticmethod
    def _create_ban_user(banUser: BanUser, user_email: str):
        new_ban_user = UserBan(
            user_email=banUser.user_email,
            admin_email=user_email,
            ban_reason=banUser.ban_reason,
            ban_start_time=datetime.now(),
            ban_end_time=datetime.now() + timedelta(days=banUser.ban_time),
        )
        return new_ban_user

    @staticmethod
    def _is_nickname_change_allowed(user: User) -> bool:
        thirty_days_ago = datetime.now(pytz.UTC) - timedelta(days=30)
        return (
            user.update_time is None
            or user.update_time.replace(tzinfo=pytz.UTC) < thirty_days_ago
        )

    @staticmethod
    def _is_nickname_duplicate(session, new_nickname: str) -> bool:
        return (
            session.query(User).filter(User.nick_name == new_nickname).first()
            is not None
        )

    @staticmethod
    def _update_nickname(session, user: User, new_nickname: str):
        user.nick_name = new_nickname
        user.update_time = datetime.now(pytz.UTC)
        session.commit()

    @staticmethod
    def _get_user_data(session, user_email: str):
        user = session.query(User).filter(User.email == user_email).first()
        grade = session.query(UserGrade).filter(UserGrade.id == user.grade).first()
        icon_list = (
            session.query(UserIcon).filter(user.email == UserIcon.user_email).first()
        )
        user_ban = (
            session.query(UserBan).filter(user.email == UserBan.user_email).first()
        )
        is_delete = (
            session.query(UserDelete).filter(user.email == UserDelete.email).first()
        )
        user_posts = session.execute(
            text(UserUtil.get_user_posts()), {"email": user_email}
        )
        comments_query = UserUtil.get_user_comment_detail()
        comments_query = text(comments_query)
        comments_param = {
            "limit": 5,
            "offset": 0,
            "user_email": user_email,
        }
        comments = session.execute(comments_query, comments_param)
        comments = [dict(row) for row in comments.mappings()]

        user_posts_list = [dict(row) for row in user_posts.mappings()]
        user_post_statistics = (
            session.query(UserPostStatistics)
            .filter(user.email == UserPostStatistics.user_email)
            .first()
        )

        user_data = {
            "user": user,
            "grade": grade.value,
            "icon_list": (icon_list.icon_list if icon_list else [default_icon]),
            "ban": (
                user_ban
                if user_ban
                else {
                    "user_email": user.email,
                    "ban_reason": None,
                    "ban_start_time": None,
                    "ban_end_time": None,
                }
            ),
            "is_delete": True if is_delete else False,
            "user_posts": user_posts_list,
            "user_comments": comments,
            "user_post_statistics": (
                user_post_statistics
                if user_post_statistics
                else {"user_email": user.email, "post_count": 0, "comment_count": 0}
            ),
        }
        return user_data

    @staticmethod
    def _get_max_pages(total_count, page_size):
        return (total_count // page_size) + (1 if total_count % page_size > 0 else 0)

    @staticmethod
    def _get_user_post_detail(session, user_email: str, page: int, page_size: int):
        cnt_params = {"user_email": user_email}
        max_cnt_query = text(UserUtil.get_user_post_detail_max_count())
        offset = (page - 1) * page_size
        result = session.execute(max_cnt_query, cnt_params)
        real_total_count = result.scalar()
        max_pages = UserFunction._get_max_pages(real_total_count, page_size)

        posts_query = UserUtil.get_user_post_detail()
        posts_query = text(posts_query)
        posts_param = {
            "limit": page_size,
            "offset": offset,
            "user_email": user_email,
        }
        posts = session.execute(posts_query, posts_param)
        posts = [dict(row) for row in posts.mappings()]

        user_query = UserUtil.get_user_info()
        user_query = text(user_query)
        user_param = {"user_email": user_email}
        user_info = session.execute(user_query, user_param)
        user_info = user_info.mappings().fetchone()

        return {
            "data": posts,
            "user_info": user_info,
            "total_count": real_total_count,
            "max_pages": max_pages,
            "current_page": page,
        }

    @staticmethod
    def _get_user_comment_detail(session, user_email: str, page: int, page_size: int):
        cnt_params = {"user_email": user_email}
        max_cnt_query = text(UserUtil.get_user_comment_detail_max_count())
        offset = (page - 1) * page_size
        result = session.execute(max_cnt_query, cnt_params)
        real_total_count = result.scalar()
        max_pages = UserFunction._get_max_pages(real_total_count, page_size)

        comments_query = UserUtil.get_user_comment_detail()
        comments_query = text(comments_query)
        comments_param = {
            "limit": page_size,
            "offset": offset,
            "user_email": user_email,
        }
        comments = session.execute(comments_query, comments_param)
        comments = [dict(row) for row in comments.mappings()]

        user_query = UserUtil.get_user_info()
        user_query = text(user_query)
        user_param = {"user_email": user_email}
        user_info = session.execute(user_query, user_param)
        user_info = user_info.mappings().fetchone()

        return {
            "data": comments,
            "user_info": user_info,
            "total_count": real_total_count,
            "max_pages": max_pages,
            "current_page": page,
        }
