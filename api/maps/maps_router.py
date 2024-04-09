from fastapi import APIRouter
from fastapi import Response
from api.maps.service import MapService

router = APIRouter()


@router.get("/three_map/{map_id}")
def get_three_map(map_id: str):
    result = Response(status_code=200, content=MapService.get_three_map(map_id))
    return result
