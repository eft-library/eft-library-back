from uuid import uuid4

from api.comment.comment_res_models import Comments
from api.comment.comment_req_models import AddComment
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
            depth=addComment.parent_depth + 1,
            create_time=datetime.now(),
            is_delete_by_admin=False,
            is_delete_by_user=False,
            like_count=0,
            dislike_count=0,
            parent_user_email=addComment.parent_user_email,
        )
        return new_comment
