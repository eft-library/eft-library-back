from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.util import UserUtil
from api.roadmap.roadmap_service import RoadmapService

router = APIRouter(tags=["Roadmap"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/get_quest")
def get_all_quest(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        return CustomResponse.response(
            RoadmapService.get_roadmap(user_email), HTTPCode.OK, Message.SUCCESS
        )
    else:
        return CustomResponse.response(
            RoadmapService.get_roadmap(None), HTTPCode.OK, Message.SUCCESS
        )
