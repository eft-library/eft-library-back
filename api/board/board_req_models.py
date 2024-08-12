from pydantic import BaseModel
from typing import List


class AddPost(BaseModel):
    """
    작성글 추가
    """

    title: str
    contents: str
    type: str


class UpdatePost(BaseModel):
    """
    작성글 수정
    """

    id: str
    title: str
    contents: str
    type: str


class LikeOrDisPost(BaseModel):
    """
    좋아요, 싫어요
    """

    id: str
    type: str
    board_type: str


class ReportBoard(BaseModel):
    """
    게시글 신고
    """

    board_id: str
    board_type: str
    reason: str


class DeletePost(BaseModel):
    """
    게시글 삭제
    """

    board_id: str
    board_type: str
