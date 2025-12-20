from pydantic import BaseModel


class CheckWpfUser(BaseModel):
    email: str


class ReqWhereAmI(BaseModel):
    email: str
    location: str
