from fastapi import APIRouter, HTTPException
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestService

router = APIRouter(tags=["Quest"])


@router.get("/all")
def get_all_quest():
    quest_list = QuestService.get_all_quest()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/feed")
def get_all_quest_detail():
    quest_list = QuestService.get_all_quest_detail()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{quest_id}")
def get_quest_by_id(quest_id: str):
    quest = QuestService.get_quest_by_id(quest_id)
    if quest is None:
        raise HTTPException(status_code=410, detail="Removed")

    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/list-with-trader/{trader_id}")
def get_quest_with_trader(trader_id: str):
    quest = QuestService.get_quest_with_trader(trader_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/all")
def get_all_quest_v3():
    quest_list = QuestService.get_all_quest_v3()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/feed")
def get_all_quest_detail_v3():
    quest_list = QuestService.get_all_quest_detail_v3()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_quest_by_normalized_name_v3(normalized_name: str):
    quest = QuestService.get_quest_by_normalized_name_v3(normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list-with-trader/{trader_normalized_name}")
def get_quest_with_trader_v3(trader_normalized_name: str):
    quest = QuestService.get_quest_with_trader_v3(trader_normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
