from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.story.service import StoryServiceV3

router = APIRouter(tags=["Story"])


@router.get("/v3/detail/{story_id}")
def get_story_by_id_v3(story_id: str):
    story_detail = StoryServiceV3.get_story_by_id_v3(story_id)
    if story_detail is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(story_detail, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/roadmap")
def get_story_roadmap_v3():
    story_roadmap = StoryServiceV3.get_story_roadmap_v3()
    if story_roadmap is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(story_roadmap, HTTPCode.OK, Message.SUCCESS)
