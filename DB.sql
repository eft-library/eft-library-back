-- 보스 정보
CREATE TABLE TKL_BOSS
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME_EN TEXT,
    NAME_KR TEXT,
    FACTION TEXT,
    LOCATION_SPAWN_CHANCE_EN JSONB,
    LOCATION_SPAWN_CHANCE_KR JSONB,
    FOLLOWERS_EN TEXT[],
    FOLLOWERS_KR TEXT[],
    IMAGE TEXT,
    HEALTH_TOTAL INTEGER,
    LOCATION_GUIDE TEXT,
    SPAWN TEXT[],
    "order" INTEGER,
    FOLLOWERS_HEALTH JSONB,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_BOSS.ID IS 'Boss ID';
COMMENT ON COLUMN TKL_BOSS.NAME_EN IS 'Boss 이름 영문';
COMMENT ON COLUMN TKL_BOSS.NAME_KR IS 'Boss 이름 한글';
COMMENT ON COLUMN TKL_BOSS.FACTION IS 'Boss 소속';
COMMENT ON COLUMN TKL_BOSS.LOCATION_SPAWN_CHANCE_EN IS 'Boss 위치 및 스폰 확률 영문';
COMMENT ON COLUMN TKL_BOSS.LOCATION_SPAWN_CHANCE_KR IS 'Boss 위치 및 스폰 확률 한글';
COMMENT ON COLUMN TKL_BOSS.FOLLOWERS_EN IS 'Boss 부하 영문';
COMMENT ON COLUMN TKL_BOSS.FOLLOWERS_KR IS 'Boss 부하 한글';
COMMENT ON COLUMN TKL_BOSS.IMAGE IS 'Boss 이미지 경로';
COMMENT ON COLUMN TKL_BOSS.HEALTH_TOTAL IS 'Boss 체력 전체';
COMMENT ON COLUMN TKL_BOSS.LOCATION_GUIDE IS 'Boss 위치 가이드';
COMMENT ON COLUMN TKL_BOSS.SPAWN IS 'Boss 스폰';
COMMENT ON COLUMN TKL_BOSS.ORDER IS 'Boss 순서';
COMMENT ON COLUMN TKL_BOSS.FOLLOWERS_HEALTH IS 'Boss 부하 체력';
COMMENT ON COLUMN TKL_BOSS.UPDATE_TIME IS 'Boss 업데이트 시간';

-- 컨테이너 정보
CREATE TABLE TKL_CONTAINER
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME_EN TEXT,
    NAME_KR TEXT,
    SHORT_NAME TEXT,
    GRIDS JSONB,
    CAPACITY INTEGER,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_CONTAINER.ID IS '컨테이너 ID';
COMMENT ON COLUMN TKL_CONTAINER.NAME_EN IS '컨테이너 이름 영문';
COMMENT ON COLUMN TKL_CONTAINER.NAME_KR IS '컨테이너 이름 한글';
COMMENT ON COLUMN TKL_CONTAINER.SHORT_NAME IS '컨테이너 짧은 이름';
COMMENT ON COLUMN TKL_CONTAINER.GRIDS IS '컨테이너 공간';
COMMENT ON COLUMN TKL_CONTAINER.CAPACITY IS '컨테이너 크기';
COMMENT ON COLUMN TKL_CONTAINER.IMAGE IS '컨테이너 이미지 경로';
COMMENT ON COLUMN TKL_CONTAINER.UPDATE_TIME IS '컨테이너 업데이트 시간';

-- 탈출구 정보
CREATE TABLE TKL_EXTRACTION
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME TEXT,
  IMAGE TEXT,
  FACTION TEXT,
  ALWAYS_AVAILABLE BOOLEAN,
  SINGLE_USE BOOLEAN,
  REQUIREMENTS jsonb,
  TIP jsonb,
  MAP TEXT,
  IMAGE_THUMBNAIL TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_EXTRACTION.ID IS '탈출구 아이디';
COMMENT ON COLUMN TKL_EXTRACTION.NAME IS '탈출구 이름';
COMMENT ON COLUMN TKL_EXTRACTION.IMAGE IS '탈출구 사진';
COMMENT ON COLUMN TKL_EXTRACTION.FACTION IS '탈출구 소속';
COMMENT ON COLUMN TKL_EXTRACTION.ALWAYS_AVAILABLE IS '탈출구 항상 열림 여부';
COMMENT ON COLUMN TKL_EXTRACTION.SINGLE_USE IS '탈출구 한 번 사용 가능 여부';
COMMENT ON COLUMN TKL_EXTRACTION.REQUIREMENTS IS '탈출구 요구사항';
COMMENT ON COLUMN TKL_EXTRACTION.TIP IS '탈출구 노트';
COMMENT ON COLUMN TKL_EXTRACTION.MAP IS '탈출구 지역';
COMMENT ON COLUMN TKL_EXTRACTION.IMAGE_THUMBNAIL IS '탈출구 썸네일';
COMMENT ON COLUMN TKL_EXTRACTION.UPDATE_TIME IS '탈출구 업데이트 시간';

-- Item Filter Categories
CREATE TABLE TKL_FILTER_CATEGORIES (
    VALUE TEXT NOT NULL PRIMARY KEY,
    EN TEXT NOT NULL,
    KR TEXT NOT NULL,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.VALUE IS 'Filter 값';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.EN IS 'Filter 영문';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.KR IS 'Filter 한글';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.UPDATE_TIME IS 'Filter 업데이트 시간';

-- Item Filter SubCategories
CREATE TABLE TKL_FILTER_SUB_CATEGORIES (
    VALUE TEXT NOT NULL PRIMARY KEY,
    EN TEXT,
    KR TEXT,
    PARENT_VALUE TEXT,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.VALUE IS 'Filter Sub 값';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.EN IS 'Filter Sub 영문';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.KR IS 'Filter Sub 한글';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.PARENT_VALUE IS 'Filter Sub 상위 키';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.IMAGE IS 'Filter Sub 이미지 주소';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.UPDATE_TIME IS 'Filter Sub 업데이트 시간';

-- provisions
CREATE TABLE TKL_PROVISIONS
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME_EN TEXT,
  NAME_KR TEXT,
  SHORT_NAME TEXT,
  CATEGORY TEXT,
  ENERGY INTEGER,
  HYDRATION INTEGER,
  STIM_EFFECTS JSONB,
  IMAGE TEXT,
  RELATED_QUESTS TEXT[],
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_PROVISIONS.ID IS '음식 아이디';
COMMENT ON COLUMN TKL_PROVISIONS.NAME_EN IS '음식 영문';
COMMENT ON COLUMN TKL_PROVISIONS.NAME_KR IS '음식 한글';
COMMENT ON COLUMN TKL_PROVISIONS.SHORT_NAME IS '음식 짧은 이름';
COMMENT ON COLUMN TKL_PROVISIONS.CATEGORY IS '음식 카테고리';
COMMENT ON COLUMN TKL_PROVISIONS.ENERGY IS '음식 에너지';
COMMENT ON COLUMN TKL_PROVISIONS.HYDRATION IS '음식 수분';
COMMENT ON COLUMN TKL_PROVISIONS.IMAGE IS '음식 이미지';
COMMENT ON COLUMN TKL_PROVISIONS.STIM_EFFECTS IS '음식 효과';
COMMENT ON COLUMN TKL_PROVISIONS.RELATED_QUESTS IS '음식 퀘스트 연관 정보';
COMMENT ON COLUMN TKL_PROVISIONS.UPDATE_TIME IS '음식 업데이트 시간';

-- Headset 정보
CREATE TABLE TKL_HEADSET
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HEADSET.ID IS 'Headset ID';
COMMENT ON COLUMN TKL_HEADSET.NAME IS 'Headset 이름';
COMMENT ON COLUMN TKL_HEADSET.SHORT_NAME IS 'Headset 짧은 이름';
COMMENT ON COLUMN TKL_HEADSET.IMAGE IS 'Headset 이미지 경로';
COMMENT ON COLUMN TKL_HEADSET.UPDATE_TIME IS 'Headset 업데이트 시간';

-- head wear 정보
CREATE TABLE TKL_HEADWEAR
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    CLASS_VALUE INTEGER,
    AREAS_EN TEXT[],
    AREAS_KR TEXT[],
    DURABILITY INTEGER,
    RICOCHET_CHANCE NUMERIC(10, 4),
    RICOCHET_STR_KR TEXT,
    RICOCHET_STR_EN TEXT,
    WEIGHT NUMERIC(10, 4),
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HEADWEAR.ID IS 'Headwear 자동 생성 ID';
COMMENT ON COLUMN TKL_HEADWEAR.NAME IS 'Headwear 이름';
COMMENT ON COLUMN TKL_HEADWEAR.SHORT_NAME IS 'Headwear 짧은 이름';
COMMENT ON COLUMN TKL_HEADWEAR.AREAS_EN IS 'Headwear 보호 부위 한글';
COMMENT ON COLUMN TKL_HEADWEAR.AREAS_KR IS 'Headwear 보호 부위 영문';
COMMENT ON COLUMN TKL_HEADWEAR.DURABILITY IS 'Headwear 내구도';
COMMENT ON COLUMN TKL_HEADWEAR.RICOCHET_CHANCE IS 'Headwear 도탄 확률';
COMMENT ON COLUMN TKL_HEADWEAR.RICOCHET_STR_KR IS 'Headwear 도탄 한글';
COMMENT ON COLUMN TKL_HEADWEAR.RICOCHET_STR_EN IS 'Headwear 도탄 영문';
COMMENT ON COLUMN TKL_HEADWEAR.CLASS_VALUE IS 'Headwear 클래스';
COMMENT ON COLUMN TKL_HEADWEAR.WEIGHT IS 'Headwear 무게';
COMMENT ON COLUMN TKL_HEADWEAR.IMAGE IS 'Headwear 이미지 경로';
COMMENT ON COLUMN TKL_HEADWEAR.UPDATE_TIME IS 'Headwear 업데이트 시간';

-- key 정보
CREATE TABLE TKL_KEY
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    USES INTEGER,
    USE_MAP_EN TEXT[],
    USE_MAP_KR TEXT[],
    MAP_VALUE TEXT[],
    RELATED_QUESTS TEXT[],
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_KEY.ID IS 'Key ID';
COMMENT ON COLUMN TKL_KEY.NAME IS 'Key 이름';
COMMENT ON COLUMN TKL_KEY.SHORT_NAME IS 'Key 짧은 이름';
COMMENT ON COLUMN TKL_KEY.IMAGE IS 'Key 이미지 경로';
COMMENT ON COLUMN TKL_KEY.USES IS 'Key 사용 횟수';
COMMENT ON COLUMN TKL_KEY.USE_MAP_EN IS 'Key 사용 맵 en';
COMMENT ON COLUMN TKL_KEY.USE_MAP_KR IS 'Key 사용 맵 kr';
COMMENT ON COLUMN TKL_KEY.MAP_VALUE IS 'Key 사용 맵 value';
COMMENT ON COLUMN TKL_KEY.RELATED_QUESTS IS 'Key 연관 퀘스트 정보';
COMMENT ON COLUMN TKL_KEY.UPDATE_TIME IS 'Key 업데이트 시간';

-- Knife 정보
CREATE TABLE TKL_KNIFE
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    CATEGORY TEXT,
    SLASH_DAMAGE INTEGER,
    STAB_DAMAGE INTEGER,
    HIT_RADIUS NUMERIC(10, 4),
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_KNIFE.ID IS 'Knife ID';
COMMENT ON COLUMN TKL_KNIFE.NAME IS 'Knife 이름';
COMMENT ON COLUMN TKL_KNIFE.SHORT_NAME IS 'Knife 짧은 이름';
COMMENT ON COLUMN TKL_KNIFE.IMAGE IS 'Knife 이미지 경로';
COMMENT ON COLUMN TKL_KNIFE.CATEGORY IS 'Knife 카테고리';
COMMENT ON COLUMN TKL_KNIFE.SLASH_DAMAGE IS 'Knife 기본 공격 데미지';
COMMENT ON COLUMN TKL_KNIFE.STAB_DAMAGE IS 'Knife 찌르기 데미지';
COMMENT ON COLUMN TKL_KNIFE.HIT_RADIUS IS 'Knife 기본 공격 범위';
COMMENT ON COLUMN TKL_KNIFE.UPDATE_TIME IS 'Knife 업데이트 날짜';


-- 전리품 정보
CREATE TABLE TKL_LOOT
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME_EN TEXT,
  NAME_KR TEXT,
  SHORT_NAME TEXT,
  IMAGE TEXT,
  CATEGORY TEXT,
  RELATED_QUESTS TEXT[],
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_LOOT.ID IS '전리품 아이디';
COMMENT ON COLUMN TKL_LOOT.NAME_EN IS '전리품 이름 영문';
COMMENT ON COLUMN TKL_LOOT.NAME_KR IS '전리품 이름 한글';
COMMENT ON COLUMN TKL_LOOT.SHORT_NAME IS '전리품 짧은 이름';
COMMENT ON COLUMN TKL_LOOT.IMAGE IS '전리품 사진';
COMMENT ON COLUMN TKL_LOOT.CATEGORY IS '전리품 카테고리 영문';
COMMENT ON COLUMN TKL_LOOT.RELATED_QUESTS IS '전리품 연관 퀘스트';
COMMENT ON COLUMN TKL_LOOT.UPDATE_TIME IS '전리품 업데이트 시간';

-- main info
CREATE TABLE TKL_MAIN
(
  VALUE TEXT NOT NULL PRIMARY KEY,
  EN_NAME TEXT,
  KR_NAME TEXT,
  LINK TEXT,
  "order" INTEGER,
  IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAIN.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_MAIN.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_MAIN.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_MAIN.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_MAIN."order" IS 'Menu 순서';
COMMENT ON COLUMN TKL_MAIN.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_MAIN.UPDATE_TIME IS 'Menu 업데이트 시간';

-- main menu 정보
CREATE TABLE TKL_MAIN_MENU
(
  VALUE TEXT NOT NULL PRIMARY KEY,
  EN_NAME TEXT NOT NULL,
  KR_NAME TEXT NOT NULL,
  LINK TEXT,
  "order" INTEGER NOT NULL,
  IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAIN_MENU.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_MAIN_MENU.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_MAIN_MENU.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_MAIN_MENU.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_MAIN_MENU."order" IS 'Menu 순서';
COMMENT ON COLUMN TKL_MAIN_MENU.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_MAIN_MENU.UPDATE_TIME IS 'Menu 업데이트 시간';

-- map dae 파일 링크 주소, item 위치 정보
CREATE TABLE TKL_MAP
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME_EN TEXT,
    NAME_KR TEXT,
    THREE_IMAGE TEXT,
    THREE_ITEM_PATH JSONB,
    JPG_IMAGE TEXT,
    JPG_ITEM_PATH JSONB,
    DEPTH INTEGER,
    "order" INTEGER,
    LINK TEXT,
    PARENT_VALUE TEXT,
    MAIN_IMAGE TEXT,
    MOT_IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAP.ID IS '3D 지도 ID';
COMMENT ON COLUMN TKL_MAP.NAME_EN IS '3D 지도 이름 영문';
COMMENT ON COLUMN TKL_MAP.NAME_KR IS '3D 지도 이름 한글';
COMMENT ON COLUMN TKL_MAP.THREE_IMAGE IS '3D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_MAP.THREE_ITEM_PATH IS '3D 지도 아이템 좌표 경로 (ThreeJS xyz)';
COMMENT ON COLUMN TKL_MAP.JPG_IMAGE IS '2D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_MAP.JPG_ITEM_PATH IS '2D 지도 아이템 좌표 경로';
COMMENT ON COLUMN TKL_MAP.DEPTH IS '지도 계층';
COMMENT ON COLUMN TKL_MAP."order" IS '3D 지도 order';
COMMENT ON COLUMN TKL_MAP.LINK IS '3D 지도 페이지 주소';
COMMENT ON COLUMN TKL_MAP.PARENT_VALUE IS '3D 지도 상위 값';
COMMENT ON COLUMN TKL_MAP.MAIN_IMAGE IS '3D 지도 썸네일';
COMMENT ON COLUMN TKL_MAP.MOT_IMAGE IS 'Map of tarkov 이미지';
COMMENT ON COLUMN TKL_MAP.UPDATE_TIME IS '3D 지도 업데이트 시간';

-- map 상위 정보
CREATE TABLE TKL_MAP_PARENT
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME_EN TEXT NOT NULL,
  NAME_KR TEXT NOT NULL,
  THREE_IMAGE TEXT NOT NULL,
  THREE_ITEM_PATH JSONB NOT NULL,
  JPG_IMAGE TEXT NOT NULL,
  JPG_ITEM_PATH JSONB NOT NULL,
  DEPTH INTEGER NOT NULL,
  "order" INTEGER NOT NULL,
  LINK TEXT NOT NULL,
  MAIN_IMAGE TEXT NOT NULL,
  MOT_IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAP_PARENT.ID IS '3D 지도 ID';
COMMENT ON COLUMN TKL_MAP_PARENT.NAME_EN IS '3D 지도 이름 영문';
COMMENT ON COLUMN TKL_MAP_PARENT.NAME_KR IS '3D 지도 이름 한글';
COMMENT ON COLUMN TKL_MAP_PARENT.THREE_IMAGE IS '3D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_MAP_PARENT.THREE_ITEM_PATH IS '3D 지도 아이템 좌표 경로 (ThreeJS xyz)';
COMMENT ON COLUMN TKL_MAP_PARENT.JPG_IMAGE IS '2D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_MAP_PARENT.JPG_ITEM_PATH IS '2D 지도 아이템 좌표 경로';
COMMENT ON COLUMN TKL_MAP_PARENT.DEPTH IS '3D 지도 단계';
COMMENT ON COLUMN TKL_MAP_PARENT.LINK IS '3D 지도 페이지 주소';
COMMENT ON COLUMN TKL_MAP_PARENT."order" IS '3D 지도 order';
COMMENT ON COLUMN TKL_MAP_PARENT.MAIN_IMAGE IS '3D 지도 썸네일';
COMMENT ON COLUMN TKL_MAP_PARENT.MOT_IMAGE IS 'Map of tarkov 이미지';
COMMENT ON COLUMN TKL_MAP_PARENT.UPDATE_TIME IS '업데이트 시간';

-- medical 정보
CREATE TABLE TKL_MEDICAL
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME_EN TEXT,
    NAME_KR TEXT,
    SHORT_NAME TEXT,
    CURES_EN TEXT[],
    CURES_KR TEXT[],
    CATEGORY TEXT,
    BUFF JSONB,
    DEBUFF JSONB,
    USE_TIME INTEGER,
    USES INTEGER,
    ENERGY_IMPACT INTEGER,
    HYDRATION_IMPACT INTEGER,
    PAINKILLER_DURATION INTEGER,
    IMAGE TEXT,
    HITPOINTS INTEGER,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MEDICAL.ID IS 'Medical ID';
COMMENT ON COLUMN TKL_MEDICAL.NAME_EN IS 'Medical 이름 영문';
COMMENT ON COLUMN TKL_MEDICAL.NAME_KR IS 'Medical 이름 한글';
COMMENT ON COLUMN TKL_MEDICAL.SHORT_NAME IS 'Medical 짧은 이름';
COMMENT ON COLUMN TKL_MEDICAL.BUFF IS 'Medical 버프 정보';
COMMENT ON COLUMN TKL_MEDICAL.DEBUFF IS 'Medical 디버프 정보';
COMMENT ON COLUMN TKL_MEDICAL.USE_TIME IS 'Medical 사용 시간';
COMMENT ON COLUMN TKL_MEDICAL.USES IS 'Medical 사용 횟수';
COMMENT ON COLUMN TKL_MEDICAL.CATEGORY IS 'Medical 카테고리';
COMMENT ON COLUMN TKL_MEDICAL.CURES_EN IS 'Medical 회복 내용 en';
COMMENT ON COLUMN TKL_MEDICAL.CURES_KR IS 'Medical 회복 내용 kr';
COMMENT ON COLUMN TKL_MEDICAL.IMAGE IS 'Medical 이미지 경로';
COMMENT ON COLUMN TKL_MEDICAL.ENERGY_IMPACT IS 'Medical 에너지';
COMMENT ON COLUMN TKL_MEDICAL.HYDRATION_IMPACT IS 'Medical 수분';
COMMENT ON COLUMN TKL_MEDICAL.PAINKILLER_DURATION IS 'Medical 지속';
COMMENT ON COLUMN TKL_MEDICAL.HITPOINTS IS 'Medical 회복량';
COMMENT ON COLUMN TKL_MEDICAL.UPDATE_TIME IS 'Medical 업데이트 시간';

-- Quest - api 데이터이고 가공용
CREATE TABLE TKL_API_QUEST
(
    id text NOT NULL PRIMARY KEY,
    name text,
    npc_name text,
    task_requirements jsonb,
    objectives jsonb,
    name_kr text,
    update_time timestamp with time zone DEFAULT now()
);
COMMENT ON COLUMN TKL_API_QUEST.id IS 'Api 퀘스트 ID';
COMMENT ON COLUMN TKL_API_QUEST.name IS 'Api 퀘스트 이름';
COMMENT ON COLUMN TKL_API_QUEST.npc_name IS 'Api 퀘스트 npc 이름';
COMMENT ON COLUMN TKL_API_QUEST.task_requirements IS 'Api 퀘스트 선행 목록';
COMMENT ON COLUMN TKL_API_QUEST.objectives IS 'Api 퀘스트 보상 목록';
COMMENT ON COLUMN TKL_API_QUEST.name_kr IS 'Api 퀘스트 이름 한글';
COMMENT ON COLUMN TKL_API_QUEST.update_time IS 'Api 퀘스트 업데이트 시간';

-- npc 정보
CREATE TABLE TKL_NPC
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME_EN TEXT NOT NULL,
  NAME_KR TEXT NOT NULL,
  IMAGE TEXT NOT NULL,
  "order" INTEGER NOT NULL,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_NPC.ID IS 'NPC 값';
COMMENT ON COLUMN TKL_NPC.NAME_EN IS 'NPC 영문';
COMMENT ON COLUMN TKL_NPC.NAME_KR IS 'NPC 한글';
COMMENT ON COLUMN TKL_NPC.IMAGE IS 'NPC 이미지 경로';
COMMENT ON COLUMN TKL_NPC."order" IS 'NPC 순서';
COMMENT ON COLUMN TKL_NPC.UPDATE_TIME IS 'NPC 업데이트 시간';

-- 퀘스트 정보
CREATE TABLE TKL_QUEST
(
    ID TEXT NOT NULL PRIMARY KEY,
    NPC_VALUE TEXT NOT NULL,
    NAME_EN TEXT NOT NULL,
    NAME_KR TEXT NOT NULL,
    OBJECTIVES_EN TEXT[] NOT NULL,
    OBJECTIVES_KR TEXT[] NOT NULL,
    REWARDS_EN TEXT[] NOT NULL,
    REWARDS_KR TEXT[] NOT NULL,
    REQUIRED_KAPPA BOOLEAN NOT NULL,
    "order" INTEGER NOT NULL,
    GUIDE TEXT,
    REQUIRES JSONB,
    NEXT JSONB,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_QUEST.ID IS 'Quest ID';
COMMENT ON COLUMN TKL_QUEST.NPC_VALUE IS 'Quest NPC 값';
COMMENT ON COLUMN TKL_QUEST.NAME_EN IS 'Quest 이름 영문';
COMMENT ON COLUMN TKL_QUEST.NAME_KR IS 'Quest 이름 한글';
COMMENT ON COLUMN TKL_QUEST.OBJECTIVES_EN IS 'Quest 목표 영문';
COMMENT ON COLUMN TKL_QUEST.OBJECTIVES_KR IS 'Quest 목표 한글';
COMMENT ON COLUMN TKL_QUEST.REWARDS_EN IS 'Quest 보상 영문';
COMMENT ON COLUMN TKL_QUEST.REWARDS_KR IS 'Quest 보상 한글';
COMMENT ON COLUMN TKL_QUEST.REQUIRED_KAPPA IS '카파 컨테이너에 필요한지 여부';
COMMENT ON COLUMN TKL_QUEST."order" IS 'Quest 순서';
COMMENT ON COLUMN TKL_QUEST.GUIDE IS 'Quest 가이드';
COMMENT ON COLUMN TKL_QUEST.REQUIRES IS 'Quest 이전 단계';
COMMENT ON COLUMN TKL_QUEST.NEXT IS 'Quest 다음 단계';
COMMENT ON COLUMN TKL_QUEST.UPDATE_TIME IS 'Quest 업데이트 시간';

-- 전술 조끼 정보
CREATE TABLE TKL_RIG
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    AREAS_EN TEXT[],
    AREAS_KR TEXT[],
    CLASS_VALUE INTEGER,
    DURABILITY INTEGER,
    CAPACITY INTEGER,
    WEIGHT NUMERIC(10, 4),
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_RIG.ID IS '전술 조끼 자동 생성 ID';
COMMENT ON COLUMN TKL_RIG.NAME IS '전술 조끼 이름';
COMMENT ON COLUMN TKL_RIG.SHORT_NAME IS '전술 조끼 짧은 이름';
COMMENT ON COLUMN TKL_RIG.AREAS_EN IS '전술 조끼 보호 부위 영문';
COMMENT ON COLUMN TKL_RIG.AREAS_KR IS '전술 조끼 보호 부위 한글';
COMMENT ON COLUMN TKL_RIG.CLASS_VALUE IS '전술 조끼 클래스';
COMMENT ON COLUMN TKL_RIG.DURABILITY IS '전술 조끼 내구도';
COMMENT ON COLUMN TKL_RIG.CAPACITY IS '전술 조끼 슬롯';
COMMENT ON COLUMN TKL_RIG.WEIGHT IS '전술 조끼 무게';
COMMENT ON COLUMN TKL_RIG.IMAGE IS '전술 조끼 이미지 경로';
COMMENT ON COLUMN TKL_RIG.UPDATE_TIME IS '전술 조끼 업데이트 시간';

-- 검색 정보
CREATE TABLE TKL_SEARCH
(
  VALUE TEXT NOT NULL,
  LINK TEXT,
  TYPE TEXT,
  PAGE_VALUE TEXT,
  "order" INTEGER,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_SEARCH.VALUE IS '검색 드롭다운 표시 값';
COMMENT ON COLUMN TKL_SEARCH.LINK IS '검색 연동 링크';
COMMENT ON COLUMN TKL_SEARCH."order" IS '검색 순서';
COMMENT ON COLUMN TKL_SEARCH.TYPE IS '검색 타입';
COMMENT ON COLUMN TKL_SEARCH.PAGE_VALUE IS '검색 페이지 값';
COMMENT ON COLUMN TKL_SEARCH.UPDATE_TIME IS '검색 업데이트 시간';

-- sub menu 정보
CREATE TABLE TKL_SUB_MENU
(
  VALUE TEXT NOT NULL PRIMARY KEY,
  EN_NAME TEXT NOT NULL,
  KR_NAME TEXT NOT NULL,
  PARENT_VALUE TEXT NOT NULL,
  LINK TEXT,
  "order" INTEGER NOT NULL,
  IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_SUB_MENU.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_SUB_MENU.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_SUB_MENU.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_SUB_MENU.PARENT_VALUE IS 'Menu 상위 값';
COMMENT ON COLUMN TKL_SUB_MENU.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_SUB_MENU."order" IS 'Menu 순서';
COMMENT ON COLUMN TKL_SUB_MENU.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_SUB_MENU.UPDATE_TIME IS 'Menu 업데이트 시간';

-- table_column 정보
CREATE TABLE TKL_TABLE_COLUMN
(
  ID TEXT NOT NULL PRIMARY KEY,
  VALUE_KR TEXT[],
  VALUE_EN TEXT[],
  JSON_VALUE JSONB,
  TYPE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_TABLE_COLUMN.ID IS 'Column 아이디';
COMMENT ON COLUMN TKL_TABLE_COLUMN.VALUE_KR IS 'Column 값 영문';
COMMENT ON COLUMN TKL_TABLE_COLUMN.VALUE_EN IS 'Column 값 한글';
COMMENT ON COLUMN TKL_TABLE_COLUMN.JSON_VALUE IS 'Column json 데이터';
COMMENT ON COLUMN TKL_TABLE_COLUMN.TYPE IS 'Column 타입';
COMMENT ON COLUMN TKL_TABLE_COLUMN.UPDATE_TIME IS 'Column 업데이트 시간';

-- throwable weapon 정보
CREATE TABLE TKL_THROWABLE
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    CATEGORY TEXT,
    FUSE NUMERIC(10, 4),
    MIN_FUSE NUMERIC(10, 4),
    MIN_EXPLOSION_DISTANCE INTEGER,
    MAX_EXPLOSION_DISTANCE INTEGER,
    FRAGMENTS INTEGER,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_THROWABLE.ID IS 'Throwable ID';
COMMENT ON COLUMN TKL_THROWABLE.NAME IS 'Throwable 이름';
COMMENT ON COLUMN TKL_THROWABLE.SHORT_NAME IS 'Throwable 짧은 이름';
COMMENT ON COLUMN TKL_THROWABLE.IMAGE IS 'Throwable 이미지 경로';
COMMENT ON COLUMN TKL_THROWABLE.CATEGORY IS 'Throwable 카테고리';
COMMENT ON COLUMN TKL_THROWABLE.FUSE IS 'Throwable 폭발 지연 시간';
COMMENT ON COLUMN TKL_THROWABLE.MIN_FUSE IS 'Throwable 폭발 지연 최소 시간';
COMMENT ON COLUMN TKL_THROWABLE.MIN_EXPLOSION_DISTANCE IS 'Throwable 최소 폭발 거리';
COMMENT ON COLUMN TKL_THROWABLE.MAX_EXPLOSION_DISTANCE IS 'Throwable 최대 폭발 거리';
COMMENT ON COLUMN TKL_THROWABLE.FRAGMENTS IS 'Throwable 파편';
COMMENT ON COLUMN TKL_THROWABLE.UPDATE_TIME IS 'Throwable 업데이트 날짜';

-- 무기 정보
CREATE TABLE TKL_WEAPON
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    CATEGORY TEXT,
    CARLIBER TEXT,
    DEFAULT_AMMO TEXT,
    MODES_EN TEXT[],
    MODES_KR TEXT[],
    FIRE_RATE INTEGER,
    ERGONOMICS INTEGER,
    RECOIL_VERTICAL INTEGER,
    RECOIL_HORIZONTAL INTEGER,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_WEAPON.ID IS 'Weapon ID';
COMMENT ON COLUMN TKL_WEAPON.NAME IS 'Weapon 이름';
COMMENT ON COLUMN TKL_WEAPON.SHORT_NAME IS 'Weapon 짧은 이름';
COMMENT ON COLUMN TKL_WEAPON.IMAGE IS 'Weapon 이미지';
COMMENT ON COLUMN TKL_WEAPON.CATEGORY IS 'Weapon 카테고리';
COMMENT ON COLUMN TKL_WEAPON.CARLIBER IS 'Weapon 탄약';
COMMENT ON COLUMN TKL_WEAPON.DEFAULT_AMMO IS 'Weapon 기본 탄약';
COMMENT ON COLUMN TKL_WEAPON.MODES_EN IS 'Weapon 발사 모드 영문';
COMMENT ON COLUMN TKL_WEAPON.MODES_KR IS 'Weapon 발사 모드 한글';
COMMENT ON COLUMN TKL_WEAPON.FIRE_RATE IS 'Weapon 발사 속도';
COMMENT ON COLUMN TKL_WEAPON.ERGONOMICS IS 'Weapon 인체공학';
COMMENT ON COLUMN TKL_WEAPON.RECOIL_VERTICAL IS 'Weapon 수직 반동';
COMMENT ON COLUMN TKL_WEAPON.RECOIL_HORIZONTAL IS 'Weapon 수평 반동';
COMMENT ON COLUMN TKL_WEAPON.UPDATE_TIME IS 'Weapon 업데이트 시간';

-- 탄약
CREATE TABLE TKL_AMMO
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME TEXT,
  SHORT_NAME TEXT,
  CATEGORY TEXT,
  ROUND TEXT,
  DAMAGE INTEGER,
  PENETRATION_POWER INTEGER,
  ARMOR_DAMAGE INTEGER,
  ACCURACY_MODIFIER NUMERIC(10, 4),
  RECOIL_MODIFIER NUMERIC(10, 4),
  LIGHT_BLEED_MODIFIER NUMERIC(10, 4),
  HEAVY_BLEED_MODIFIER NUMERIC(10, 4),
  EFFICIENCY INTEGER[],
  IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_AMMO.ID IS '탄약 아이디';
COMMENT ON COLUMN TKL_AMMO.NAME IS '탄약 영문';
COMMENT ON COLUMN TKL_AMMO.SHORT_NAME IS '탄약 영문';
COMMENT ON COLUMN TKL_AMMO.CATEGORY IS '탄약 카테고리';
COMMENT ON COLUMN TKL_AMMO.ROUND IS '탄약 종류';
COMMENT ON COLUMN TKL_AMMO.DAMAGE IS '탄약 데미지';
COMMENT ON COLUMN TKL_AMMO.PENETRATION_POWER IS '탄약 관통력';
COMMENT ON COLUMN TKL_AMMO.ARMOR_DAMAGE IS '탄약 방어구 피해량';
COMMENT ON COLUMN TKL_AMMO.ACCURACY_MODIFIER IS '탄약 정확성';
COMMENT ON COLUMN TKL_AMMO.RECOIL_MODIFIER IS '탄약 반동';
COMMENT ON COLUMN TKL_AMMO.LIGHT_BLEED_MODIFIER IS '탄약 가벼운 출혈';
COMMENT ON COLUMN TKL_AMMO.HEAVY_BLEED_MODIFIER IS '탄약 깊은 출혈';
COMMENT ON COLUMN TKL_AMMO.EFFICIENCY IS '탄약 방어 등급 효율성';
COMMENT ON COLUMN TKL_AMMO.IMAGE IS '탄약 사진';
COMMENT ON COLUMN TKL_AMMO.UPDATE_TIME IS '탄약 업데이트 시간';

-- 배낭 정보
CREATE TABLE TKL_BACKPACK
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    GRIDS JSONB,
    CAPACITY INTEGER,
    WEIGHT NUMERIC(10, 4),
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_BACKPACK.ID IS '배낭 ID';
COMMENT ON COLUMN TKL_BACKPACK.NAME IS '배낭 이름';
COMMENT ON COLUMN TKL_BACKPACK.SHORT_NAME IS '배낭 짧은 이름';
COMMENT ON COLUMN TKL_BACKPACK.GRIDS IS '배낭 공간';
COMMENT ON COLUMN TKL_BACKPACK.CAPACITY IS '배낭 크기';
COMMENT ON COLUMN TKL_BACKPACK.WEIGHT IS '배낭 무게';
COMMENT ON COLUMN TKL_BACKPACK.IMAGE IS '배낭 이미지 경로';
COMMENT ON COLUMN TKL_BACKPACK.UPDATE_TIME IS '배낭 업데이트 시간';

-- 방탄 조끼 정보
CREATE TABLE TKL_ARMOR_VEST
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    AREAS_EN TEXT[],
    AREAS_KR TEXT[],
    CLASS_VALUE INTEGER,
    DURABILITY INTEGER,
    WEIGHT NUMERIC(10, 4),
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_ARMOR_VEST.ID IS '방탄 조끼 ID';
COMMENT ON COLUMN TKL_ARMOR_VEST.NAME IS '방탄 조끼 이름';
COMMENT ON COLUMN TKL_ARMOR_VEST.SHORT_NAME IS '방탄 조끼 짧은 이름';
COMMENT ON COLUMN TKL_ARMOR_VEST.AREAS_EN IS '방탄 조끼 보호 부위 영문';
COMMENT ON COLUMN TKL_ARMOR_VEST.AREAS_KR IS '방탄 조끼 보호 부위 한글';
COMMENT ON COLUMN TKL_ARMOR_VEST.CLASS_VALUE IS '방탄 조끼 클래스';
COMMENT ON COLUMN TKL_ARMOR_VEST.DURABILITY IS '방탄 조끼 내구도';
COMMENT ON COLUMN TKL_ARMOR_VEST.WEIGHT IS '방탄 조끼 무게';
COMMENT ON COLUMN TKL_ARMOR_VEST.IMAGE IS '방탄 조끼 이미지 경로';
COMMENT ON COLUMN TKL_ARMOR_VEST.UPDATE_TIME IS '방탄 조끼 업데이트 시간';

-- 백 발생한 에러 적재
CREATE SEQUENCE SEQ_TKL_BACK_LOG START 1;
CREATE TABLE TKL_BACK_LOG
(
    BACK_LOG_ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_BACK_LOG') NOT NULL PRIMARY KEY,
    BACK_LOG_MESSAGE TEXT,
    BACK_LOG_OCCUR_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_BACK_LOG.BACK_LOG_ID IS 'Backend 로그 자동 생성 ID';
COMMENT ON COLUMN TKL_BACK_LOG.BACK_LOG_MESSAGE IS 'Backend 에러 로그 메시지';
COMMENT ON COLUMN TKL_BACK_LOG.BACK_LOG_OCCUR_TIME IS 'Backend 에러 로그 발생 시간';

-- 프론트 발생한 에러 적재
CREATE SEQUENCE SEQ_TKL_FRONT_LOG START 1;
CREATE TABLE TKL_FRONT_LOG
(
    FRONT_LOG_ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_FRONT_LOG') NOT NULL PRIMARY KEY,
    FRONT_LOG_MESSAGE TEXT,
    FRONT_LOG_OCCUR_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FRONT_LOG.FRONT_LOG_ID IS 'Frontend 로그 자동 생성 ID';
COMMENT ON COLUMN TKL_FRONT_LOG.FRONT_LOG_MESSAGE IS 'Frontend 에러 로그 메시지';
COMMENT ON COLUMN TKL_FRONT_LOG.FRONT_LOG_OCCUR_TIME IS 'Frontend 에러 로그 발생 시간';

-- hideout master
CREATE TABLE TKL_HIDEOUT_MASTER
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME_EN TEXT,
    NAME_KR TEXT,
    IMAGE TEXT,
    LEVEL_IDS TEXT[],
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.ID IS 'Hideout 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.NAME_EN IS 'Hideout 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.NAME_KR IS 'Hideout 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.IMAGE IS 'Hideout 이미지';
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.LEVEL_IDS IS 'Hideout level 아이디 리스트';
COMMENT ON COLUMN TKL_HIDEOUT_MASTER.UPDATE_TIME IS 'Hideout 업데이트 시간';

-- hideout item require
CREATE TABLE TKL_HIDEOUT_ITEM_REQUIRE
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL_ID TEXT,
    NAME_EN TEXT,
    NAME_KR TEXT,
    QUANTITY INTEGER,
    COUNT INTEGER,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.ID IS 'Hideout item require 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.LEVEL_ID IS 'Hideout item require 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.NAME_EN IS 'Hideout item require 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.NAME_KR IS 'Hideout item require 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.QUANTITY IS 'Hideout item require 양';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.COUNT IS 'Hideout item require 개수';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.IMAGE IS 'Hideout item require 이미지';
COMMENT ON COLUMN TKL_HIDEOUT_ITEM_REQUIRE.UPDATE_TIME IS 'Hideout item require 업데이트 시간';

-- hideout level
CREATE TABLE TKL_HIDEOUT_LEVEL
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL INTEGER,
    CONSTRUCTION_TIME INTEGER,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_LEVEL.ID IS 'Hideout level 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_LEVEL.ID IS 'Hideout level 값';
COMMENT ON COLUMN TKL_HIDEOUT_LEVEL.ID IS 'Hideout level 건축 시간';
COMMENT ON COLUMN TKL_HIDEOUT_LEVEL.UPDATE_TIME IS 'Hideout level 업데이트 시간';

-- hideout trader
CREATE TABLE TKL_HIDEOUT_TRADER_REQUIRE
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL_ID TEXT,
    NAME_EN TEXT,
    NAME_KR TEXT,
    COMPARE TEXT,
    REQUIRE_TYPE TEXT,
    VALUE INTEGER,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.ID IS 'Hideout trader 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.LEVEL_ID IS 'Hideout trader 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.NAME_EN IS 'Hideout trader 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.NAME_KR IS 'Hideout trader 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.COMPARE IS 'Hideout trader 비교 수식';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.REQUIRE_TYPE IS 'Hideout trader 요구 타입';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.VALUE IS 'Hideout trader 값';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.IMAGE IS 'Hideout trader 이미지';
COMMENT ON COLUMN TKL_HIDEOUT_TRADER_REQUIRE.UPDATE_TIME IS 'Hideout trader 업데이트 시간';

-- hideout station require
CREATE TABLE TKL_HIDEOUT_STATION_REQUIRE
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL_ID TEXT,
    LEVEL INTEGER,
    NAME_EN TEXT,
    NAME_KR TEXT,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.ID IS 'Hideout station require 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.LEVEL_ID IS 'Hideout station require 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.LEVEL IS 'Hideout station require 레벨';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.NAME_EN IS 'Hideout station require 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.NAME_KR IS 'Hideout station require 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.IMAGE IS 'Hideout station require 이미지';
COMMENT ON COLUMN TKL_HIDEOUT_STATION_REQUIRE.UPDATE_TIME IS 'Hideout station require 업데이트 시간';

-- hideout crafts
CREATE TABLE TKL_HIDEOUT_CRAFTS
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL_ID TEXT,
    LEVEL INTEGER,
    NAME_EN TEXT,
    NAME_KR TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.ID IS 'Hideout crafts 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.LEVEL_ID IS 'Hideout crafts 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.LEVEL IS 'Hideout crafts 레벨';
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.NAME_EN IS 'Hideout crafts 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.NAME_KR IS 'Hideout crafts 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_CRAFTS.UPDATE_TIME IS 'Hideout crafts 업데이트 시간';

-- hideout skill require
CREATE TABLE TKL_HIDEOUT_SKILL_REQUIRE
(
    ID TEXT NOT NULL PRIMARY KEY,
    LEVEL_ID TEXT,
    LEVEL INTEGER,
    NAME_EN TEXT,
    NAME_KR TEXT,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.ID IS 'Hideout skill require 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.LEVEL_ID IS 'Hideout skill require 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.LEVEL IS 'Hideout skill require 레벨';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.NAME_EN IS 'Hideout skill require 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.NAME_KR IS 'Hideout skill require 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.IMAGE IS 'Hideout skill require 사진';
COMMENT ON COLUMN TKL_HIDEOUT_SKILL_REQUIRE.UPDATE_TIME IS 'Hideout skill require 업데이트 시간';

-- hideout bonus
CREATE TABLE TKL_HIDEOUT_BONUS
(
    LEVEL_ID TEXT NOT NULL,
    TYPE TEXT NOT NULL,
    NAME_EN TEXT,
    NAME_KR TEXT,
    VALUE NUMERIC(10, 4),
    SKILL_NAME_EN TEXT,
    SKILL_NAME_KR TEXT,
    UPDATE_TIME timestamp with time zone default now(),
    PRIMARY KEY (LEVEL_ID, TYPE)
);
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.LEVEL_ID IS 'Hideout bonus 레벨 아이디';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.TYPE IS 'Hideout bonus 타입';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.NAME_EN IS 'Hideout bonus 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.NAME_KR IS 'Hideout bonus 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.VALUE IS 'Hideout bonus 값';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.SKILL_NAME_EN IS 'Hideout bonus 스킬 이름 영문';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.SKILL_NAME_KR IS 'Hideout bonus 스킬 이름 한글';
COMMENT ON COLUMN TKL_HIDEOUT_BONUS.UPDATE_TIME IS 'Hideout bonus 아이디';

-- 아이템 연관 퀘스트 요구 사항
CREATE TABLE TKL_RELATED_QUEST
(
  ITEM_ID TEXT,
  QUEST_ID TEXT,
  ITEM_NAME TEXT,
  QUEST_NAME TEXT,
  TYPE TEXT,
  IN_RAID BOOLEAN,
  DESC_TEXT TEXT[],
  ITEM_IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now(),
  PRIMARY KEY (ITEM_ID, QUEST_ID)
);
COMMENT ON COLUMN TKL_RELATED_QUEST.ITEM_ID IS '아이템 연관 퀘스트 정보 아이템 아이디';
COMMENT ON COLUMN TKL_RELATED_QUEST.QUEST_ID IS '아이템 연관 퀘스트 정보 퀘스트 아이디';
COMMENT ON COLUMN TKL_RELATED_QUEST.ITEM_NAME IS '아이템 연관 퀘스트 정보 아이템 이름';
COMMENT ON COLUMN TKL_RELATED_QUEST.QUEST_NAME IS '아이템 연관 퀘스트 정보 퀘스트 이름';
COMMENT ON COLUMN TKL_RELATED_QUEST.TYPE IS '아이템 연관 퀘스트 정보 퀘스트 아이템 타입';
COMMENT ON COLUMN TKL_RELATED_QUEST.IN_RAID IS '아이템 연관 퀘스트 정보 아이템 인 레이드 여부';
COMMENT ON COLUMN TKL_RELATED_QUEST.DESC_TEXT IS '아이템 연관 퀘스트 정보 설명';
COMMENT ON COLUMN TKL_RELATED_QUEST.ITEM_IMAGE IS '아이템 연관 퀘스트 정보 아이템 이미지';
COMMENT ON COLUMN TKL_RELATED_QUEST.UPDATE_TIME IS '아이템 연관 퀘스트 정보 업데이트 시간';

-- News 정보
CREATE TABLE TKL_NEWS
(
  GAME_VERSION TEXT primary key ,
  ARENA_VERSION TEXT,
  PATCH_LINK TEXT,
  EVENT_LINK TEXT,
  YOUTUBE_ID TEXT,
  NEXT_UPDATE TEXT[],
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_NEWS.GAME_VERSION IS '뉴스 게임 버전';
COMMENT ON COLUMN TKL_NEWS.ARENA_VERSION IS '뉴스 아레나 버전';
COMMENT ON COLUMN TKL_NEWS.PATCH_LINK IS '뉴스 패치 주소';
COMMENT ON COLUMN TKL_NEWS.EVENT_LINK IS '뉴스 이벤트 주소';
COMMENT ON COLUMN TKL_NEWS.YOUTUBE_ID IS '뉴스 유튜브 아이디';
COMMENT ON COLUMN TKL_NEWS.NEXT_UPDATE IS '뉴스 다음 업데이트 리스트';
COMMENT ON COLUMN TKL_NEWS.UPDATE_TIME IS '뉴스 업데이트 시간';

-- 보스 전리품
CREATE TABLE TKL_BOSS_LOOT
(
  ITEM_ID TEXT,
  BOSS_ID TEXT,
  ITEM_NAME TEXT,
  BOSS_NAME TEXT,
  TYPE TEXT,
  ITEM_IMAGE TEXT,
  UPDATE_TIME timestamp with time zone default now(),
  PRIMARY KEY (ITEM_ID, BOSS_ID)
);
COMMENT ON COLUMN TKL_BOSS_LOOT.ITEM_ID IS '보스 전리품 아이템 아이디';
COMMENT ON COLUMN TKL_BOSS_LOOT.BOSS_ID IS '보스 전리품 보스 아이디';
COMMENT ON COLUMN TKL_BOSS_LOOT.ITEM_NAME IS '보스 전리품 아이템 이름';
COMMENT ON COLUMN TKL_BOSS_LOOT.BOSS_NAME IS '보스 전리품 보스 이름';
COMMENT ON COLUMN TKL_BOSS_LOOT.TYPE IS '보스 전리품 아이템 타입';
COMMENT ON COLUMN TKL_BOSS_LOOT.ITEM_IMAGE IS '보스 전리품 아이템 이미지';
COMMENT ON COLUMN TKL_BOSS_LOOT.UPDATE_TIME IS '보스 전리품 업데이트 시간';
