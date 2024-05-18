from enum import Enum


class Message(Enum):
    SUCCESS = 'OK'
    MAP_NOT_FOUND = 'Map not found'
    YOUTUBE_NOT_FOUND = 'Youtube not found'
    MENU_NOT_FOUND = 'Menu not found'
    NPC_NOT_FOUND = 'NPC not found'
    QUEST_NOT_FOUND = 'Quest not found'
    WEAPON_NOT_FOUND = 'Weapon not found'
    MAIN_INFO_NOT_FOUND = "Main info not found"
