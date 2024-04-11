from fastapi import APIRouter
from api.maps.service import MapService
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter()

MAP_NOT_FOUND = 'Map not found'
SUCCESS = 'OK'


@router.get("/three_map/{map_id}")
def get_three_map(map_id: str):
    three_map = MapService.get_three_map(map_id)
    if three_map is None:
        return CustomResponse.response(None, HTTPCode.OK, MAP_NOT_FOUND)
    return CustomResponse.response(three_map, HTTPCode.OK, SUCCESS)


@router.get("/three_map")
def get_all_three_map():
    three_maps = MapService.get_all_three_map()
    if three_maps is None:
        return CustomResponse.response(None, HTTPCode.OK, MAP_NOT_FOUND)
    return CustomResponse.response(three_maps, HTTPCode.OK, SUCCESS)


@router.get("/jpg_map/{map_id}")
def get_jpg_map(map_id: str):
    jpg_map = MapService.get_jpg_map(map_id)
    if jpg_map is None:
        return CustomResponse.response(None, HTTPCode.OK, MAP_NOT_FOUND)
    return CustomResponse.response(jpg_map, HTTPCode.OK, SUCCESS)


@router.get("/jpg_map")
def get_all_jpg_map():
    jpg_maps = MapService.get_all_jpg_map()
    if jpg_maps is None:
        return CustomResponse.response(None, HTTPCode.OK, MAP_NOT_FOUND)
    return CustomResponse.response(jpg_maps, HTTPCode.OK, SUCCESS)
