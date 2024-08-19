from sqlalchemy import text

from api.user.user_req_models import AddUserReq, BanUser
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from api.user.user_function import UserFunction
from api.user.util import UserUtil

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

    @staticmethod
    def user_ban(banUser: BanUser, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_ban_user = UserFunction._create_ban_user(banUser, user_email)
                s.add(new_ban_user)
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_user_post_detail(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                posts_query = UserUtil.get_user_post_detail()
                posts_query = text(posts_query)
                posts_param = {"user_email": user_email}
                posts = s.execute(posts_query, posts_param)
                posts = [dict(row) for row in posts.mappings()]

                user_query = UserUtil.get_user_info()
                user_query = text(user_query)
                user_param = {"user_email": user_email}
                user_info = s.execute(user_query, user_param)
                user_info = user_info.mappings().fetchone()

                result = {"posts": posts, "user_info": user_info}

                return result
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_user_comment_detail(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                comments_query = UserUtil.get_user_comment_detail()
                comments_query = text(comments_query)
                comments_param = {"user_email": user_email}
                comments = s.execute(comments_query, comments_param)
                comments = [dict(row) for row in comments.mappings()]

                user_query = UserUtil.get_user_info()
                user_query = text(user_query)
                user_param = {"user_email": user_email}
                user_info = s.execute(user_query, user_param)
                user_info = user_info.mappings().fetchone()

                result = {"comments": comments, "user_info": user_info}

                return result
        except Exception as e:
            print("오류 발생:", e)
            return None
