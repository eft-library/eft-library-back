from datetime import datetime

from sqlalchemy import text, and_
from api.comment.comment_res_models import (
    Comments,
    CommentLike,
    CommentDisLike,
)
from database import DataBaseConnector
from api.comment.comment_req_models import (
    AddComment,
    DeleteComment,
    LikeOrDisComment,
    ReportComment,
    UpdateComment,
)
from api.comment.util import CommentUtil
from api.comment.comment_function import CommentFunction
from api.board.board_function import BoardFunction


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
    def update_comment(updateComment: UpdateComment):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                comment = (
                    s.query(Comments).filter(Comments.id == updateComment.id).first()
                )
                clean_html = BoardFunction._remove_video_delete_button(
                    updateComment.contents
                )
                comment.contents = clean_html
                comment.update_time = datetime.now()
                s.commit()

                return clean_html
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_comment_by_id(page: int, page_size: int, board_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                max_count = (
                    s.query(Comments).filter(Comments.board_id == board_id).count()
                )
                offset = (page - 1) * page_size

                where_clause = CommentUtil.comment_where_clause(False)
                query = CommentUtil.get_comment_query()
                query = query.format(where_clause=where_clause)
                query = text(query)

                params = {
                    "limit": page_size,
                    "offset": offset,
                    "board_id": board_id,
                    "user_email": user_email,
                }
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

    @staticmethod
    def like_or_dis_comment(likeOrDisComment: LikeOrDisComment, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                comment = (
                    s.query(Comments).filter(Comments.id == likeOrDisComment.id).first()
                )

                like_comment = (
                    s.query(CommentLike)
                    .filter(
                        and_(
                            CommentLike.user_email == user_email,
                            CommentLike.comment_id == likeOrDisComment.id,
                        )
                    )
                    .first()
                )

                dislike_comment = (
                    s.query(CommentDisLike)
                    .filter(
                        and_(
                            CommentDisLike.user_email == user_email,
                            CommentDisLike.comment_id == likeOrDisComment.id,
                        )
                    )
                    .first()
                )

                if likeOrDisComment.type == "like":
                    CommentFunction._handle_like(
                        s,
                        comment,
                        likeOrDisComment,
                        like_comment,
                        dislike_comment,
                        user_email,
                    )
                else:
                    CommentFunction._handle_dislike(
                        s,
                        comment,
                        likeOrDisComment,
                        like_comment,
                        dislike_comment,
                        user_email,
                    )

                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def report_comment(reportComment: ReportComment, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_report = CommentFunction._create_comment_report(
                    reportComment, user_email
                )
                s.add(new_report)
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_issue_comment_by_id(board_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                where_clause = CommentUtil.comment_where_clause(True)
                query = CommentUtil.get_comment_query()
                query = query.format(where_clause=where_clause)
                query = text(query)

                params = {
                    "board_id": board_id,
                    "user_email": user_email,
                }
                result = s.execute(query, params).fetchall()
                comments = [dict(row._mapping) for row in result]

                return {
                    "data": comments,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_issue_comment_page(board_id: str, comment_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 댓글 rank 조회
                limit_count = 10
                comment_rank_query = CommentUtil.get_issue_comment_rank_query()
                rank_params = {
                    "comment_id": comment_id,
                    "board_id": board_id,
                }
                comment_rank_query = text(comment_rank_query)
                rank_result = s.execute(comment_rank_query, rank_params)
                comment_rank = rank_result.scalar()
                page = (comment_rank - 1) // limit_count + 1
                offset = (page - 1) * limit_count

                max_count = (
                    s.query(Comments).filter(Comments.board_id == board_id).count()
                )

                where_clause = CommentUtil.comment_where_clause(False)
                query = CommentUtil.get_comment_query()
                query = query.format(where_clause=where_clause)
                query = text(query)

                params = {
                    "limit": limit_count,
                    "offset": offset,
                    "board_id": board_id,
                    "user_email": user_email,
                }
                result = s.execute(query, params).fetchall()
                max_pages = CommentFunction._get_max_pages(max_count, limit_count)
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
