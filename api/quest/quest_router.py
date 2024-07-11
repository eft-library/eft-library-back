from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestService

router = APIRouter(tags=["Quest"])


@router.get("/npc")
def get_npc():
    npc_list = QuestService.get_all_npc()
    if npc_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.NPC_NOT_FOUND)
    return CustomResponse.response(npc_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/all")
def get_all_quest():
    quest_list = QuestService.get_all_quest_preview()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{quest_id}")
def get_quest_by_id(quest_id: str):
    quest = QuestService.get_quest_by_id(quest_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/select")
def get_user_select_quest():
    quest = QuestService.get_user_select_quest()
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
