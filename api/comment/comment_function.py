from uuid import uuid4

from api.comment.comment_res_models import (
    Comments,
    CommentLike,
    CommentDisLike,
    CommentReport,
)
from api.comment.comment_req_models import AddComment, ReportComment
from datetime import datetime


class CommentFunction:
    @staticmethod
    def _get_max_pages(real_total_count, page_size):
        return (real_total_count // page_size) + (
            1 if real_total_count % page_size > 0 else 0
        )

    @staticmethod
    def _make_comment(addComment: AddComment, user_email: str):
        new_comment = Comments(
            id=uuid4(),
            board_id=addComment.board_id,
            user_email=user_email,
            board_type=addComment.board_type,
            parent_id=addComment.parent_id,
            contents=addComment.contents,
            depth=addComment.depth,
            create_time=datetime.now(),
            is_delete_by_admin=False,
            is_delete_by_user=False,
            like_count=0,
            dislike_count=0,
            parent_user_email=addComment.parent_user_email,
        )
        return new_comment

    @staticmethod
    def _handle_like(
        s, comment, likeOrDisComment, like_comment, dislike_comment, user_email
    ):
        if like_comment:
            comment.like_count -= 1
            s.delete(like_comment)
        elif dislike_comment:
            comment.like_count += 1
            comment.dislike_count -= 1
            s.delete(dislike_comment)
            new_like_comment = CommentLike(
                comment_id=likeOrDisComment.id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            s.add(new_like_comment)
        else:
            comment.like_count += 1
            new_like_comment = CommentLike(
                comment_id=likeOrDisComment.id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            s.add(new_like_comment)
        s.commit()

    @staticmethod
    def _handle_dislike(
        s, comment, likeOrDisComment, like_comment, dislike_comment, user_email
    ):
        if like_comment:
            comment.like_count -= 1
            comment.dislike_count += 1
            new_dislike_comment = CommentDisLike(
                comment_id=likeOrDisComment.id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            s.delete(like_comment)
            s.add(new_dislike_comment)
        elif dislike_comment:
            comment.dislike_count -= 1
            s.delete(dislike_comment)
        else:
            comment.dislike_count += 1
            new_dislike_comment = CommentDisLike(
                comment_id=likeOrDisComment.id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            s.add(new_dislike_comment)
        s.commit()

    @staticmethod
    def _create_comment_report(reportComment: ReportComment, user_email: str):
        new_report = CommentReport(
            comment_id=reportComment.comment_id,
            report_reason=reportComment.reason,
            report_user=user_email,
            create_time=datetime.now(),
        )
        return new_report
