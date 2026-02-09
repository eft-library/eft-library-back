from typing import Optional

from fastapi import APIRouter, Depends
from api.response import CustomResponse
from api.roadmap.roadmap_req_models import GetRoadMap, SaveRoadmap
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.util import UserUtil
from api.roadmap.roadmap_service import RoadmapService

router = APIRouter(tags=["Roadmap"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/get-quest")
def get_all_quest(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = RoadmapService.get_roadmap(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/save-roadmap",
    include_in_schema=False,
)
def save_roadmap(roadmap: SaveRoadmap, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = RoadmapService.save_roadmap(roadmap.questList, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
