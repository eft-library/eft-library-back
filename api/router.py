from fastapi import APIRouter
from api.map import map_router
from api.news import news_router
from api.menu import menu_router
from api.quest import quest_router

api_router = APIRouter()

api_router.include_router(map_router.router, prefix="/map")
api_router.include_router(news_router.router, prefix="/news")
api_router.include_router(menu_router.router, prefix="/menu")
api_router.include_router(quest_router.router, prefix="/quest")

