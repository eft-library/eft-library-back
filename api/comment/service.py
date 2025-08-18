from api.comment.util import CommentUtil
from database import DataBaseConnector
from sqlalchemy import text
from nanoid import generate


class CommentService:
    @staticmethod
    def insert_parent_comment(post_id: str, contents: str, user_email: str):
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
                    "user_email": user_email,
                }
                s.execute(insert_comment_query, insert_comment_params)

                return {"result": 1}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def inset_child_comment(
        post_id: str, parent_comment_id: str, contents: str, user_email: str
    ):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # nano id 생성
                new_id = generate(size=12)

                insert_comment_query = text(CommentUtil.insert_child_comment())
                insert_comment_params = {
                    "comment_id": new_id,
                    "parent_comment_id": parent_comment_id,
                    "post_id": post_id,
                    "contents": contents,
                    "user_email": user_email,
                }
                s.execute(insert_comment_query, insert_comment_params)

                return {"result": 1}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_comment(post_id: str, page_num: int):
        try:
            limit = 20
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rn_start = (page_num - 1) * limit + 1
                rn_end = page_num + limit
                get_comment_query = text(CommentUtil.get_comment())
                get_comment_param = {
                    "post_id": post_id,
                    "rn_start": rn_start,
                    "rn_edn": rn_end,
                }
                comments = s.execute(get_comment_query, get_comment_param)

                total_query = text(CommentUtil.get_comment_total_count())
                total_result = s.execute(total_query, {"post_id": post_id})
                total = total_result.scalar()

                max_page_count = (total + limit - 1) // limit

                return {
                    "comments": comments,
                    "total": total,
                    "max_page_count": max_page_count,
                }
        except Exception as e:
            print("오류 발생:", e)
            return None
