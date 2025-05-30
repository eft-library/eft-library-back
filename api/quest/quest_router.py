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
        return CustomResponse.response(None, HTTPCode.OK, Message.NPC_NOT_FOUND)
    return CustomResponse.response(npc_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/all")
def get_all_quest():
    quest_list = QuestService.get_all_quest()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/feed")
def get_all_quest_detail():
    quest_list = QuestService.get_all_quest_detail()
    if quest_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{quest_id}")
def get_quest_by_id(quest_id: str):
    # 예전 ID 목록 또는 예전 ID 판별 조건
    deprecated_ids = {
        "59c124d686f774189b3c843f",
        "5d25e45e86f77408251c4bfa",
        "addquest28",
        "5a27bc8586f7741b543d8ea4",
        "5c0be13186f7746f016734aa",
        "5969f9e986f7741dde183a50",
        "66058cb7c7f3584787181476",
        "5a68661a86f774500f48afb0",
        "63a88045abf76d719f42d715",
        "60e71e8ed54b755a3b53eb67",
        "63a5cf262964a7488f5243ce",
        "64ee9df4496db64f9b7a4432",
        "5ae4493d86f7744b8e15aa8f",
        "5edabd13218d181e29451442",
        "5c0be5fc86f774467a116593",
        "63966fd9ea19ac7ed845db30",
        "639135f286e646067c176a87",
        "63966fe7ea74a47c2d3fc0e6",
        "5bc480a686f7741af0342e29",
        "64f5aac4b63b74469b6c14c2",
        "5b47799d86f7746c5d6a5fd8",
        "5ae3270f86f77445ba41d4dd",
        "5a0327ba86f77456b9154236",
        "5a27b75b86f7742e97191958",
        "5ac346cf86f7741d63233a02",
        "5b47926a86f7747ccc057c15",
        "59ca2eb686f77445a80ed049",
        "5c0d0f1886f77457b8210226",
        "5d25e2b486f77409de05bba0",
        "5ac2426c86f774138762edfe",
        "forklift_certified",
        "5ae448bf86f7744d733e55ee",
        "addquest36",
        "black_swan",
        "596760e186f7741e11214d58",
        "5a0449d586f77474e66227b7",
        "64f5deac39e45b527a7c4232",
        "63a9b36cc31b00242d28a99f",
        "marathon_-_new_day,_new_paths",
        "addquest3",
        "639282134ed9512be67647ed",
        "5d25e2a986f77409dd5cdf2a",
        "test_drive_-_part_5",
        "5ac3462b86f7741d6118b983",
        "597a0e5786f77426d66c0636",
        "657315df034d76585f032e01",
        "5d25e48186f77443e625e386",
        "5c139eb686f7747878361a6f",
        "63913715f8e5dd32bf4e3aaa",
        "6086c852c945025d41566124",
        "63a511ea30d85e10e375b045",
        "639135e0fa894f0a866afde6",
        "5d25c81b86f77443e625dd71",
        "5a27bafb86f7741c73584017",
        "63a9ae24009ffc6a551631a5",
        "63966ff54c3ef01b6f3ffad8",
        "6179b3a12153c15e937d52bc",
        "639135c3744e452011470807",
        "639135d89444fb141f4e6eea",
        "5a68663e86f774501078f78a",
        "5c51aac186f77432ea65c552",
        "639136e84ed9512be67647db",
        "625d70031ed3bb5bcc5bd9e5",
        "addquest5",
        "5ac3464c86f7741d651d6877",
        "5c1128e386f7746565181106",
        "5d25d2c186f77443e35162e5",
        "64e7b9bffd30422ed03dad38",
        "5ae449b386f77446d8741719",
        "63966fbeea19ac7ed845db2e",
        "5b478eca86f7744642012254",
        "5ae3267986f7742a413592fe",
        "60effd818b669d08a35bfad5",
        "639136d68ba6894d155e77cf",
        "5edaba7c0c502106f869bc02",
        "5b478d0f86f7744d190d91b5",
        "5c0bdb5286f774166e38eed4",
        "638fcd23dc65553116701d33",
        "625d6ff5ddc94657c21a1625",
        "1234",
        "5d24b81486f77439c92d6ba8",
        "6179afd0bca27a099552e040",
        "null",
        "leatherman-multitool",
        "overseas-trust-part-1",
    }

    if quest_id in deprecated_ids:
        raise HTTPException(status_code=410, detail="This quest is permanently gone")

    quest = QuestService.get_quest_by_id(quest_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)

    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)


@router.get("/list/{npc_id}")
def get_quest_by_npc(npc_id: str):
    quest = QuestService.get_quest_by_npc(npc_id)
    if quest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.QUEST_NOT_FOUND)
    return CustomResponse.response(quest, HTTPCode.OK, Message.SUCCESS)
