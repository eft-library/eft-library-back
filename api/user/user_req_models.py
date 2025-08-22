from pydantic import BaseModel


class AddUserReq(BaseModel):
    """
    사용자 추가 시
    """

    id: str
    name: str
    email: str
    image: str


class UpdateUserNickname(BaseModel):
    nickname: str
