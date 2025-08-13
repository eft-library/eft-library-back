from pydantic import BaseModel


class CreateCommunity(BaseModel):
    title: str
    category: str
    contents: str


class UpdateCommunity(CreateCommunity):
    id: int


class ViewCount(BaseModel):
    post_id: int


class PostReaction(BaseModel):
    post_id: int
    reaction_type: str


class GetPostDetail(BaseModel):
    url: str
    user_email: str
