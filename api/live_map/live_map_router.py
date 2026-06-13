from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from api.constants import Message
from api.live_map.service import LiveMapServiceV3
from api.roadmap.roadmap_req_models import SaveRoadmap
from api.roadmap.roadmap_service import RoadmapServiceV3
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["Live Map"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/v3/detail/{normalized_name}")
def get_live_map_v3(normalized_name: str):
    live_map = LiveMapServiceV3.get_live_map_v3(normalized_name)
    if live_map is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(live_map, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/quest/{quest_id_or_normalized_name}")
def get_live_map_quest_detail_v3(quest_id_or_normalized_name: str):
    quest = LiveMapServiceV3.get_quest_detail_v3(quest_id_or_normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/story/{story_id}")
def get_live_map_story_detail_v3(story_id: str):
    story = LiveMapServiceV3.get_story_detail_v3(story_id)
    if story is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(story, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/event/{event_id}")
def get_live_map_event_detail_v3(event_id: str):
    event = LiveMapServiceV3.get_event_detail_v3(event_id)
    if event is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(event, HTTPCode.OK, Message.SUCCESS)


@router.get(
    "/v3/user-roadmap",
    include_in_schema=False,
)
def get_live_map_user_roadmap_v3(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)

    user_roadmap = RoadmapServiceV3.get_user_roadmap_v3(user_email)
    if user_roadmap is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(user_roadmap, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/save-roadmap",
    include_in_schema=False,
)
def save_live_map_roadmap_v3(
    roadmap: SaveRoadmap, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = RoadmapServiceV3.save_roadmap_v3(roadmap.questList, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
