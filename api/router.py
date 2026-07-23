from fastapi import APIRouter
from api.map import map_router
from api.news import news_router
from api.quest import quest_router
from api.boss import boss_router
from api.map_of_tarkov import map_of_tarkov_router
from api.search import search_router
from api.item import item_router
from api.hideout import hideout_router
from api.user import user_router
from api.roadmap import roadmap_router
from api.price import price_router
from api.dashboard import dashboard_router
from api.home import home_router
from api.community import community_router
from api.comment import comment_router
from api.where_am_i import where_am_i_router
from api.progress import progress_router
from api.minigame import minigame_router
from api.story import story_router
from api.chat import chat_router
from api.live_map import live_map_router
from api.kord_breach import router as kord_breach_router
from api.deployment_notice import router as deployment_notice_router

api_router = APIRouter()

api_router.include_router(home_router.router, prefix="/home")
api_router.include_router(news_router.router, prefix="/news")
api_router.include_router(search_router.router, prefix="/search")
api_router.include_router(map_router.router, prefix="/map")
api_router.include_router(map_of_tarkov_router.router, prefix="/map-of-tarkov")
api_router.include_router(boss_router.router, prefix="/boss")
api_router.include_router(quest_router.router, prefix="/quest")
api_router.include_router(item_router.router, prefix="/item")
api_router.include_router(user_router.router, prefix="/user")
api_router.include_router(roadmap_router.router, prefix="/roadmap")
api_router.include_router(hideout_router.router, prefix="/hideout")
api_router.include_router(price_router.router, prefix="/price")
api_router.include_router(dashboard_router.router, prefix="/dashboard")
api_router.include_router(community_router.router, prefix="/community")
api_router.include_router(comment_router.router, prefix="/comment")
api_router.include_router(where_am_i_router.router, prefix="/where-am-i")
api_router.include_router(progress_router.router, prefix="/progress")
api_router.include_router(minigame_router.router, prefix="/minigame")
api_router.include_router(story_router.router, prefix="/story")
api_router.include_router(chat_router.router, prefix="/chat")
api_router.include_router(live_map_router.router, prefix="/live-map")
api_router.include_router(kord_breach_router.router, prefix="/kord-breach")
api_router.include_router(deployment_notice_router.router, prefix="/deployment-notice")
