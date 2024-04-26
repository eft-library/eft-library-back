from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.quest.service import QuestService

router = APIRouter()


@router.get("/npc")
def get_npc():
    npc_list = QuestService.get_all_npc()
    if npc_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.NPC_NOT_FOUND)
    return CustomResponse.response(npc_list, HTTPCode.OK, Message.SUCCESS)
