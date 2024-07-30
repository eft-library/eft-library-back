from pydantic import BaseModel
from typing import List


class AddPost(BaseModel):
    """
    작성글 추가
    """

    title: str
    contents: str
    type: str
