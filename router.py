from fastapi import APIRouter
from api.maps import maps_router

api_router = APIRouter()

api_router.include_router(maps_router.router, prefix="/maps")

