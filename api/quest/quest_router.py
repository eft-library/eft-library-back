from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestService

router = APIRouter(tags=["Quest"])


@router.get("/v3/completion-graph")
def get_completion_graph():
    completion_graph = QuestService.get_completion_graph()
    if completion_graph is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(completion_graph, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/all")
def get_all_quest():
    quest_list = QuestService.get_all_quest()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/feed")
def get_all_quest_detail():
    quest_list = QuestService.get_all_quest_detail()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_quest_by_normalized_name(normalized_name: str):
    quest = QuestService.get_quest_by_normalized_name(normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list-with-trader/{trader_normalized_name}")
def get_quest_with_trader(trader_normalized_name: str):
    quest = QuestService.get_quest_with_trader(trader_normalized_name)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
