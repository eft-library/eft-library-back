from pydantic import BaseModel

class CreateCommunity(BaseModel):
    title: str
    category: str
    user_email: str
    contents: str

class UpdateCommunity(CreateCommunity):
    id: int

class ViewCount(BaseModel):
    post_id: int

class PostReaction(BaseModel):
    post_id: int
    user_email: str
    reaction_type: str