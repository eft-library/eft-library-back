from fastapi import APIRouter
from api.news.service import NewsService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter()


@router.get("/youtube")
def get_youtube():
    three_map = NewsService.get_youtube()
    if three_map is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.YOUTUBE_NOT_FOUND)
    return CustomResponse.response(three_map, HTTPCode.OK, Message.SUCCESS)

