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
                # 전체 개수 조회
                total_query = text(CommentUtil.get_comment_total_count())
                total_result = s.execute(total_query, {"post_id": post_id})
                total = total_result.scalar()

                # 최대 페이지 수
                max_page_count = (total + limit - 1) // limit

                # 마지막 페이지 요청 (page_num == 0)
                if page_num == 0:
                    current_page_num = max_page_count
                else:
                    current_page_num = page_num

                # rn_start, rn_end 계산
                rn_start = (current_page_num - 1) * limit + 1
                rn_end = current_page_num * limit

                get_comment_query = text(CommentUtil.get_comment())
                get_comment_param = {
                    "post_id": post_id,
                    "rn_start": rn_start,
                    "rn_end": rn_end,
                }
                comments = s.execute(get_comment_query, get_comment_param)

                return {
                    "comments": comments,
                    "total": total,
                    "max_page_count": max_page_count,
                    "current_page_num": current_page_num,
                }
        except Exception as e:
            print("오류 발생:", e)
            return None
