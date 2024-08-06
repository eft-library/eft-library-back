from enum import Enum


class Message(Enum):
    SUCCESS = "OK"
    MAP_NOT_FOUND = "Map not found"
    NEWS_NOT_FOUND = "News not found"
    MENU_NOT_FOUND = "Menu not found"
    NPC_NOT_FOUND = "NPC not found"
    QUEST_NOT_FOUND = "Quest not found"
    EVENT_NOT_FOUND = "Event not found"
    POSTS_NOT_FOUND = "Posts not found"
    BOARD_TYPE_NOT_FOUND = "Board type not found"
    IMAGE_UPLOAD_FAIL = "Image upload fail"
    PATCH_NOTES_NOT_FOUND = "Patch notes not found"
    WEAPON_NOT_FOUND = "Weapon not found"
    MAIN_INFO_NOT_FOUND = "Main info not found"
    BOSS_NOT_FOUND = "Boss not found"
    MAP_OF_TARKOV_NOT_FOUND = "Map of tarkov not found"
    COLUMN_NOT_FOUND = "Column not found"
    SEARCH_NOT_FOUND = "SEARCH not found"
    SITE_LIST_NOT_FOUND = "Site list not found"
    ITEM_FILTER_NOT_FOUND = "Item filter not found"
    HEADSET_NOT_FOUND = "Headset not found"
    HEADWEAR_NOT_FOUND = "Headwear not found"
    ARMOR_VEST_NOT_FOUND = "Armor vest not found"
    RIG_NOT_FOUND = "Rig not found"
    BACKPACK_NOT_FOUND = "Backpack not found"
    CONTAINER_NOT_FOUND = "Container not found"
    KEY_NOT_FOUND = "Key not found"
    PROVISION_NOT_FOUND = "Provisions not found"
    MEDICAL_NOT_FOUND = "Medical not found"
    AMMO_NOT_FOUND = "Ammo not found"
    LOOT_NOT_FOUND = "Loot not found"
    GLASSES_NOT_FOUND = "Glasses not found"
    FACE_COVER_NOT_FOUND = "Face cover not found"
    ARM_BAND_NOT_FOUND = "Arm band not found"
    HIDEOUT_NOT_FOUND = "Hideout not found"
    USER_ADD_FAIL = "User add fail"
    USER_DELETE_FAIL = "User delete fail"
    INVALID_USER = "Invalid User"
    SUCCESS_QUEST_FAIL = "Success quest fail"
    NICKNAME_DUPLICATE = "Nickname is duplicate"
    NICKNAME_CHANGE_NOT_AVAILABLE = "Available after 30 days."
    ADD_BOARD_FAIL = "Add board fail"
    POST_LIKE_CHANGE_FAIL = "Post like change fail"
    USER_POSTS_NOT_FOUND = "User posts not found"
