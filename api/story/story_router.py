from fastapi import APIRouter, HTTPException
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.story.service import StoryServices

router = APIRouter(tags=["Story"])


@router.get("/detail/{story_id}")
def get_story_by_id(story_id: str):
    story_detail = StoryServices.get_story_by_id(story_id)
    if story_detail is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(story_detail, HTTPCode.OK, Message.SUCCESS)
