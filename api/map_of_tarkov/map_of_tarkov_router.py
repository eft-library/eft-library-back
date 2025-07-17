from fastapi import APIRouter
from api.map_of_tarkov.service import MapOfTarkovService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map Of Tarkov"])


@router.get("/selector")
def get_map_selector():
    map_of_tarkov = MapOfTarkovService.get_map_selector()
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)


@router.get("/info/{map_id}")
def get_map_info(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_map_info(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)


@router.get("/boss/{map_id}")
def get_boss_info(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_boss_info(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)


@router.get("/extraction/{map_id}")
def get_extraction_info(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_extraction_info(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)


@router.get("/transits/{map_id}")
def get_transits_info(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_transits_info(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)


@router.get("/find/{map_id}")
def get_find_info(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_find_info(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)

@router.get("/detail/{map_id}")
def get_map_of_tarkov(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_map_of_tarkov(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND
        )
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)