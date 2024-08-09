from sqlalchemy import text
from api.comment.comment_res_models import Comments
from database import DataBaseConnector
from api.comment.comment_req_models import AddComment, DeleteComment
from api.comment.util import CommentUtil
from api.comment.comment_function import CommentFunction


class CommentService:
    @staticmethod
    def add_comment(addComment: AddComment, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_comment = CommentFunction._make_comment(addComment, user_email)
                s.add(new_comment)
                s.commit()

                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_comment_by_id(page: int, page_size: int, board_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                max_count = (
                    s.query(Comments).filter(Comments.board_id == board_id).count()
                )
                offset = (page - 1) * page_size
                query = text(CommentUtil.get_comment_query())
                params = {"limit": page_size, "offset": offset, "board_id": board_id}
                result = s.execute(query, params).fetchall()
                max_pages = CommentFunction._get_max_pages(max_count, page_size)
                comments = [dict(row._mapping) for row in result]

                return {
                    "data": comments,
                    "total_count": max_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def delete_comment(deleteComment: DeleteComment):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                comment = (
                    s.query(Comments)
                    .filter(Comments.id == deleteComment.comment_id)
                    .first()
                )
                if deleteComment.delete_by_user:
                    comment.is_delete_by_user = True
                else:
                    comment.is_delete_by_admin = True
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None
