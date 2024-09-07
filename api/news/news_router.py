from fastapi import APIRouter
from api.news.service import NewsService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["News"])


@router.get("/news")
def get_news():
    news = NewsService.get_news()
    if news is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.NEWS_NOT_FOUND)
    return CustomResponse.response(news, HTTPCode.OK, Message.SUCCESS)


@router.get("/popup")
def get_popup():
    popup = NewsService.get_popup()
    if popup is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POPUP_NOT_FOUND)
    return CustomResponse.response(popup, HTTPCode.OK, Message.SUCCESS)
