from pydantic import BaseModel


class AddComment(BaseModel):
    """
    댓글 추가
    """

    parent_id: str
    contents: str
    board_type: str
    board_id: str
    parent_depth: int
