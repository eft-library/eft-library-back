from api.comment.util import CommentUtil
from database import DataBaseConnector
from sqlalchemy import text
from nanoid import generate


class CommentService:
    @staticmethod
    def insert_parent_comment(post_id: str, contents: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # nano id 생성
                new_id = generate(size=12)

                insert_comment_query = text(CommentUtil.insert_parent_comment())
                insert_comment_params = {
                    "comment_id": new_id,
                    "post_id": post_id,
                    "contents": contents,
                }
                return None
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def inset_child_comment():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                return None
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_comment():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # page num이랑, total 등 필요
                return None
        except Exception as e:
            print("오류 발생:", e)
            return None
