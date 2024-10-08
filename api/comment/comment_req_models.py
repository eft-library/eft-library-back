from pydantic import BaseModel


class AddComment(BaseModel):
    """
    댓글 추가
    """

    parent_id: str
    contents: str
    board_type: str
    board_id: str
    depth: int
    parent_user_email: str


class UpdateComment(BaseModel):
    """
    댓글 수정
    """

    id: str
    contents: str


class DeleteComment(BaseModel):
    """
    댓글 삭제
    """

    delete_by_user: bool
    comment_id: str


class LikeOrDisComment(BaseModel):
    """
    좋아요, 싫어요
    """

    id: str
    type: str


class ReportComment(BaseModel):
    """
    댓글 신고
    """

    comment_id: str
    reason: str
