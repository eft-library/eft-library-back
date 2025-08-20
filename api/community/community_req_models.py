from pydantic import BaseModel


class CreateCommunity(BaseModel):
    title: str
    category: str
    contents: str


class UpdateCommunity(CreateCommunity):
    id: str


class ViewCount(BaseModel):
    post_id: str


class PostReaction(BaseModel):
    post_id: str


class PostBookmark(BaseModel):
    post_id: str


class PostDelete(BaseModel):
    post_id: str


class FollowUser(BaseModel):
    following_user_email: str


class CheckFollow(BaseModel):
    following_user_email: str
    user_email: str


class GetPostDetail(BaseModel):
    url: str
    user_email: str
    page_category: str
