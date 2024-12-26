from fastapi import APIRouter, Depends
from api.response import CustomResponse
from api.roadmap.roadmap_req_models import GetRoadMap
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.util import UserUtil
from api.roadmap.roadmap_service import RoadmapService

router = APIRouter(tags=["Roadmap"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/get_quest")
def get_all_quest(getRoadMap: GetRoadMap):
    result = RoadmapService.get_roadmap(getRoadMap.user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
