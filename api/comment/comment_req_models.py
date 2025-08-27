from pydantic import BaseModel


class InsertParentComment(BaseModel):
    post_id: str
    contents: str


class InsertChildComment(InsertParentComment):
    parent_comment_id: str
    contents: str
    post_id: str


class UpdateComment(BaseModel):
    comment_id: str
    contents: str


class DeleteComment(BaseModel):
    comment_id: str


class CommentReaction(BaseModel):
    comment_id: str


class GetComments(BaseModel):
    post_id: str
    issue_comment_id: str
    page_num: int
    user_email: str


class ReqCommentReport(BaseModel):
    comment_id: str
    reported_email: str
    reason_type: str
    reason: str
