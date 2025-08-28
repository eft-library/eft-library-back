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


class ReqUserReport(BaseModel):
    reported_email: str
    reason_type: str
    reason: str


class ReqUserBlock(BaseModel):
    blocker_email: str
    blocked_email: str
    reason: str
