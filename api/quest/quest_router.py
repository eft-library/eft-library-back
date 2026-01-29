from fastapi import APIRouter, HTTPException
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestService

router = APIRouter(tags=["Quest"])


@router.get("/npc")
def get_npc():
    npc_list = QuestService.get_npc_selector()
    if npc_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(npc_list, HTTPCode.OK, Message.SUCCESS)


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


@router.get("/list/{npc_id}")
def get_quest_by_npc(npc_id: str):
    quest = QuestService.get_quest_by_npc(npc_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/list-with-trader/{trader_id}")
def get_quest_with_trader(trader_id: str):
    quest = QuestService.get_quest_with_trader(trader_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
