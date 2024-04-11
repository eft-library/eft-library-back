from fastapi import APIRouter
from api.map import map_router

api_router = APIRouter()

api_router.include_router(map_router.router, prefix="/map")

