from fastapi import APIRouter
from api.map import map_router
from api.news import news_router

api_router = APIRouter()

api_router.include_router(map_router.router, prefix="/map")
api_router.include_router(news_router.router, prefix="/news")

