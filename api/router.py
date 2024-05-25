from fastapi import APIRouter
from api.map import map_router
from api.news import news_router
from api.menu import menu_router
from api.quest import quest_router
from api.weapon import weapon_router
from api.boss import boss_router
from api.map_of_tarkov import map_of_tarkov_router

api_router = APIRouter()

api_router.include_router(map_router.router, prefix="/map")
api_router.include_router(news_router.router, prefix="/news")
api_router.include_router(menu_router.router, prefix="/menu")
api_router.include_router(quest_router.router, prefix="/quest")
api_router.include_router(weapon_router.router, prefix="/weapon")
api_router.include_router(boss_router.router, prefix="/boss")
api_router.include_router(map_of_tarkov_router.router, prefix="/map_of_tarkov")
