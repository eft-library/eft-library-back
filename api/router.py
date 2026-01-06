from fastapi import APIRouter
from api.map import map_router
from api.news import news_router
from api.quest import quest_router
from api.boss import boss_router
from api.map_of_tarkov import map_of_tarkov_router
from api.dynamic_info import dynamic_info_router
from api.search import search_router
from api.item_filter import item_filter_router
from api.item import item_router
from api.hideout import hideout_router
from api.user import user_router
from api.event import event_router
from api.patch_notes import patch_notes_router
from api.notice import notice_router
from api.roadmap import roadmap_router
from api.price import price_router
from api.planner import planner_router
from api.dashboard import dashboard_router
from api.home import home_router
from api.menu import menu_router
from api.community import community_router
from api.comment import comment_router
from api.where_am_i import where_am_i_router
from api.progress import progress_router

api_router = APIRouter()

api_router.include_router(map_router.router, prefix="/map")
api_router.include_router(news_router.router, prefix="/news")
api_router.include_router(menu_router.router, prefix="/menu")
api_router.include_router(home_router.router, prefix="/home")
api_router.include_router(quest_router.router, prefix="/quest")
api_router.include_router(boss_router.router, prefix="/boss")
api_router.include_router(map_of_tarkov_router.router, prefix="/map-of-tarkov")
api_router.include_router(dynamic_info_router.router, prefix="/dynamic-info")
api_router.include_router(search_router.router, prefix="/search")
api_router.include_router(item_filter_router.router, prefix="/item-filter")
api_router.include_router(item_router.router, prefix="/item")
api_router.include_router(user_router.router, prefix="/user")
api_router.include_router(planner_router.router, prefix="/planner")
api_router.include_router(roadmap_router.router, prefix="/roadmap")
api_router.include_router(hideout_router.router, prefix="/hideout")
api_router.include_router(event_router.router, prefix="/event")
api_router.include_router(patch_notes_router.router, prefix="/patch-notes")
api_router.include_router(notice_router.router, prefix="/notice")
api_router.include_router(price_router.router, prefix="/price")
api_router.include_router(dashboard_router.router, prefix="/dashboard")
api_router.include_router(community_router.router, prefix="/community")
api_router.include_router(comment_router.router, prefix="/comment")
api_router.include_router(where_am_i_router.router, prefix="/where-am-i")
api_router.include_router(progress_router.router, prefix="/progress")
