from pydantic import BaseModel


class InsertParentComment(BaseModel):
    post_id: str
    contents: str


class InsertChildComment(InsertParentComment):
    parent_comment_id: str
