from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestServiceV3

router = APIRouter(tags=["Quest"])


@router.get("/v3/all")
def get_all_quest_v3():
    quest_list = QuestServiceV3.get_all_quest_v3()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/feed")
def get_all_quest_detail_v3():
    quest_list = QuestServiceV3.get_all_quest_detail_v3()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_quest_by_normalized_name_v3(normalized_name: str):
    quest = QuestServiceV3.get_quest_by_normalized_name_v3(normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list-with-trader/{trader_normalized_name}")
def get_quest_with_trader_v3(trader_normalized_name: str):
    quest = QuestServiceV3.get_quest_with_trader_v3(trader_normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
