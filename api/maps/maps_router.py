from fastapi import APIRouter, HTTPException
from api.maps.service import MapService
from api.response import CustomResponse

router = APIRouter()


@router.get("/three_map/{map_id}")
def get_three_map(map_id: str):
    three_map = MapService.get_three_map(map_id)
    if three_map is None:
        return CustomResponse.response(None, 200, "Map not found")
    return CustomResponse.response(three_map, 200, "OK")
