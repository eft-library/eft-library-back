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

-- tarkov youtube 업데이트 소식
CREATE TABLE TKL_YOUTUBE
(
    ID VARCHAR(30) NOT NULL PRIMARY KEY,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_YOUTUBE.ID IS 'Youtube 링크 ID';
COMMENT ON COLUMN TKL_YOUTUBE.UPDATE_TIME IS 'DB 업데이트 시간';

-- map 상위 정보
CREATE TABLE TKL_MAP_PARENT
(
  ID VARCHAR(50) NOT NULL PRIMARY KEY,
  NAME_EN VARCHAR(50) NOT NULL,
  NAME_KR VARCHAR(50) NOT NULL,
  THREE_IMAGE TEXT NOT NULL,
  THREE_ITEM_PATH JSONB NOT NULL,
  JPG_IMAGE TEXT NOT NULL,
  JPG_ITEM_PATH JSONB NOT NULL,
  DEPTH INTEGER NOT NULL,
  ORDER INTEGER NOT NULL,
  LINK VARCHAR(60) NOT NULL,
  MAIN_IMAGE VARCHAR(50) NOT NULL,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_PARENT.ID IS '3D 지도 ID';
COMMENT ON COLUMN TKL_PARENT.NAME_EN IS '3D 지도 이름 영문';
COMMENT ON COLUMN TKL_PARENT.NAME_KR IS '3D 지도 이름 한글';
COMMENT ON COLUMN TKL_PARENT.THREE_IMAGE IS '3D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_PARENT.THREE_ITEM_PATH IS '3D 지도 아이템 좌표 경로 (ThreeJS xyz)';
COMMENT ON COLUMN TKL_PARENT.JPG_IMAGE IS '2D 지도 nas 저장 경로';
COMMENT ON COLUMN TKL_PARENT.JPG_ITEM_PATH IS '2D 지도 아이템 좌표 경로';
COMMENT ON COLUMN TKL_PARENT.DEPTH IS '3D 지도 단계';
COMMENT ON COLUMN TKL_PARENT.LINK IS '3D 지도 페이지 주소';
COMMENT ON COLUMN TKL_PARENT.ORDER IS '3D 지도 order';
COMMENT ON COLUMN TKL_PARENT.MAIN_IMAGE IS '3D 지도 썸네일';
COMMENT ON COLUMN TKL_PARENT.UPDATE_TIME IS '업데이트 시간';

-- map dae 파일 링크 주소, item 위치 정보
CREATE TABLE TKL_MAP
(
    ID VARCHAR(50) NOT NULL PRIMARY KEY,
    NAME_EN VARCHAR(50) NOT NULL,
    NAME_KR VARCHAR(50) NOT NULL,
    THREE_IMAGE TEXT NOT NULL,
    THREE_ITEM_PATH JSONB NOT NULL,
    JPG_IMAGE TEXT NOT NULL,
    JPG_ITEM_PATH JSONB NOT NULL,
    DEPTH INTEGER NOT NULL,
    ORDER INTEGER NOT NULL,
    LINK VARCHAR(60) NOT NULL,
    PARENT_VALUE VARCHAR(50) NOT NULL,
    MAIN_IMAGE VARCHAR(50) NOT NULL,
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
COMMENT ON COLUMN TKL_MAP.ORDER IS '3D 지도 order';
COMMENT ON COLUMN TKL_MAP.LINK IS '3D 지도 페이지 주소';
COMMENT ON COLUMN TKL_MAP.PARENT_VALUE IS '3D 지도 상위 값';
COMMENT ON COLUMN TKL_MAP.MAIN_IMAGE IS '3D 지도 썸네일';
COMMENT ON COLUMN TKL_MAP.UPDATE_TIME IS '3D 지도 업데이트 시간';

-- 가방 정보
CREATE SEQUENCE SEQ_TKL_BAG START 1;
CREATE TABLE TKL_BAG
(
    ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_BAG') NOT NULL PRIMARY KEY,
    NAME_EN VARCHAR(80) NOT NULL,
    NAME_KR VARCHAR(80) NOT NULL,
    GRID_SIZE VARCHAR(10) NOT NULL,
    SLOTS INTEGER NOT NULL,
    LAYOUT VARCHAR(100)[] NOT NULL,
    SOLD_BY_EN VARCHAR(100)[] NOT NULL,
    SOLD_BY_KR VARCHAR(100)[] NOT NULL,
    MOVEMENT_SPEED INTEGER NOT NULL,
    TURNING_SPEED INTEGER NOT NULL,
    ERGONOMICS INTEGER NOT NULL,
    WEIGHT NUMERIC(10, 4) NOT NULL,
    IMAGE TEXT NOT NULL,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_BAG.ID IS '가방 자동 생성 ID';
COMMENT ON COLUMN TKL_BAG.NAME_EN IS '가방 이름 영문';
COMMENT ON COLUMN TKL_BAG.NAME_KR IS '가방 이름 한글';
COMMENT ON COLUMN TKL_BAG.GRID_SIZE IS '가방 그리드 크기';
COMMENT ON COLUMN TKL_BAG.SLOTS IS '가방 슬롯 크기';
COMMENT ON COLUMN TKL_BAG.LAYOUT IS '가방 구조';
COMMENT ON COLUMN TKL_BAG.SOLD_BY_EN IS '가방 판매처 영문';
COMMENT ON COLUMN TKL_BAG.SOLD_BY_KR IS '가방 판매처 한글';
COMMENT ON COLUMN TKL_BAG.MOVEMENT_SPEED IS '가방 장착시 이동 속도';
COMMENT ON COLUMN TKL_BAG.TURNING_SPEED IS '가방 장착시 회전 속도';
COMMENT ON COLUMN TKL_BAG.ERGONOMICS IS '가방 인체 공학 설계';
COMMENT ON COLUMN TKL_BAG.WEIGHT IS '가방 무게';
COMMENT ON COLUMN TKL_BAG.IMAGE IS '가방 이미지 경로';
COMMENT ON COLUMN TKL_BAG.UPDATE_TIME IS '가방 업데이트 시간';

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

-- 퀘스트 정보
CREATE SEQUENCE SEQ_TKL_QUEST START 1;
CREATE TABLE TKL_QUEST
(
    ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_QUEST') NOT NULL PRIMARY KEY,
    NPC_VALUE VARCHAR(20) NOT NULL,
    NAME_EN VARCHAR(80) NOT NULL,
    NAME_KR VARCHAR(80) NOT NULL,
    OBJECTIVES_EN VARCHAR(100)[] NOT NULL,
    OBJECTIVES_KR VARCHAR(100)[] NOT NULL,
    REWARDS_EN VARCHAR(100)[] NOT NULL,
    REWARDS_KR VARCHAR(100)[] NOT NULL,
    REQUIRED_KAPPA BOOLEAN NOT NULL,
    ORDER INTEGER NOT NULL,
    GUIDE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_QUEST.ID IS 'Quest 자동 생성 ID';
COMMENT ON COLUMN TKL_QUEST.NPC_VALUE IS 'Quest NPC 값';
COMMENT ON COLUMN TKL_QUEST.NAME_EN IS 'Quest 이름 영문';
COMMENT ON COLUMN TKL_QUEST.NAME_KR IS 'Quest 이름 한글';
COMMENT ON COLUMN TKL_QUEST.OBJECTIVES_EN IS 'Quest 목표 영문';
COMMENT ON COLUMN TKL_QUEST.OBJECTIVES_KR IS 'Quest 목표 한글';
COMMENT ON COLUMN TKL_QUEST.REWARDS_EN IS 'Quest 보상 영문';
COMMENT ON COLUMN TKL_QUEST.REWARDS_KR IS 'Quest 보상 한글';
COMMENT ON COLUMN TKL_QUEST.REQUIRED_KAPPA IS '카파 컨테이너에 필요한지 여부';
COMMENT ON COLUMN TKL_QUEST.ORDER IS 'Quest 순서';
COMMENT ON COLUMN TKL_QUEST.GUIDE IS 'Quest 가이드';
COMMENT ON COLUMN TKL_QUEST.UPDATE_TIME IS 'Quest 업데이트 시간';

-- npc 정보
CREATE TABLE TKL_NPC
(
  ID VARCHAR(20) NOT NULL PRIMARY KEY,
  NAME_EN VARCHAR(20) NOT NULL,
  NAME_KR VARCHAR(20) NOT NULL,
  IMAGE TEXT NOT NULL,
  ORDER INTEGER NOT NULL,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_NPC.ID IS 'NPC 값';
COMMENT ON COLUMN TKL_NPC.NAME_EN IS 'NPC 영문';
COMMENT ON COLUMN TKL_NPC.NAME_KR IS 'NPC 한글';
COMMENT ON COLUMN TKL_NPC.IMAGE IS 'NPC 이미지 경로';
COMMENT ON COLUMN TKL_NPC.ORDER IS 'NPC 순서';
COMMENT ON COLUMN TKL_NPC.UPDATE_TIME IS 'NPC 업데이트 시간';

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
COMMENT ON COLUMN TKL_KEY.UPDATE_TIME IS 'Key 업데이트 시간';

-- 보스 정보
CREATE SEQUENCE SEQ_TKL_BOSS START 1;
CREATE TABLE TKL_BOSS
(
    ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_BOSS') NOT NULL PRIMARY KEY,
    NAME_EN VARCHAR(20) NOT NULL,
    NAME_KR VARCHAR(20) NOT NULL,
    FACTION VARCHAR(15) NOT NULL,
    LOCATION_SPAWN_CHANCE_EN JSONB NOT NULL,
    LOCATION_SPAWN_CHANCE_KR JSONB NOT NULL,
    FOLLOWERS_EN VARCHAR(20)[] NOT NULL,
    FOLLOWERS_KR VARCHAR(20)[] NOT NULL,
    IMAGE TEXT NOT NULL,
    HEALTH_IMAGE TEXT[] NOT NULL,
    HEALTH_TOTAL INTEGER NOT NULL,
    LOCATION_GUIDE TEXT NOt NULL,
    LOOT TEXT[] NOT NULL,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_BOSS.ID IS 'Boss 자동 생성 ID';
COMMENT ON COLUMN TKL_BOSS.NAME_EN IS 'Boss 이름 영문';
COMMENT ON COLUMN TKL_BOSS.NAME_KR IS 'Boss 이름 한글';
COMMENT ON COLUMN TKL_BOSS.FACTION IS 'Boss 소속';
COMMENT ON COLUMN TKL_BOSS.LOCATION_SPAWN_CHANCE_EN IS 'Boss 위치 및 스폰 확률 영문';
COMMENT ON COLUMN TKL_BOSS.LOCATION_SPAWN_CHANCE_KR IS 'Boss 위치 및 스폰 확률 한글';
COMMENT ON COLUMN TKL_BOSS.FOLLOWERS_EN IS 'Boss 부하 영문';
COMMENT ON COLUMN TKL_BOSS.FOLLOWERS_KR IS 'Boss 부하 한글';
COMMENT ON COLUMN TKL_BOSS.IMAGE IS 'Boss 이미지 경로';
COMMENT ON COLUMN TKL_BOSS.HEALTH_IMAGE IS 'Boss 체력 이미지 경로';
COMMENT ON COLUMN TKL_BOSS.HEALTH_TOTAL IS 'Boss 체력 전체';
COMMENT ON COLUMN TKL_BOSS.LOCATION_GUIDE IS 'Boss 위치 가이드';
COMMENT ON COLUMN TKL_BOSS.LOOT IS 'Boss 전리품';
COMMENT ON COLUMN TKL_BOSS.UPDATE_TIME IS 'Boss 업데이트 시간';

-- Knife 정보
CREATE TABLE TKL_KNIFE
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    CATEGORY VARCHAR(40),
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

-- throwable weapon 정보
CREATE TABLE TKL_THROWABLE
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    CATEGORY VARCHAR(40),
    FUSE NUMERIC(10, 4),
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
COMMENT ON COLUMN TKL_THROWABLE.MIN_EXPLOSION_DISTANCE IS 'Throwable 최소 폭발 거리';
COMMENT ON COLUMN TKL_THROWABLE.MAX_EXPLOSION_DISTANCE IS 'Throwable 최대 폭발 거리';
COMMENT ON COLUMN TKL_THROWABLE.FRAGMENTS IS 'Throwable 파편';
COMMENT ON COLUMN TKL_THROWABLE.UPDATE_TIME IS 'Throwable 업데이트 날짜';

-- 하이드아웃 정보
CREATE SEQUENCE SEQ_TKL_HIDEOUT START 1;
CREATE TABLE TKL_HIDEOUT
(
    ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_HIDEOUT') NOT NULL PRIMARY KEY,
    NAME VARCHAR(30) NOT NULL,
    LEVEL INTEGER NOT NULL,
    REQUIREMENTS_EN VARCHAR(100)[] NOT NULL,
    REQUIREMENTS_KR VARCHAR(100)[] NOT NULL,
    FUNCTION_EN VARCHAR(100)[] NOT NULL,
    FUNCTION_KR VARCHAR(100)[] NOT NULL,
    UPGRADE_TIME VARCHAR(10) NOT NULL,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HIDEOUT.ID IS 'Hideout 자동 생성 ID';
COMMENT ON COLUMN TKL_HIDEOUT.NAME IS 'Hideout 이름';
COMMENT ON COLUMN TKL_HIDEOUT.LEVEL IS 'Hideout 레벨';
COMMENT ON COLUMN TKL_HIDEOUT.REQUIREMENTS_EN IS 'Hideout 건설 요구 사항 영문';
COMMENT ON COLUMN TKL_HIDEOUT.REQUIREMENTS_KR IS 'Hideout 건설 요구 사항 한글';
COMMENT ON COLUMN TKL_HIDEOUT.FUNCTION_EN IS 'Hideout 효과 영문';
COMMENT ON COLUMN TKL_HIDEOUT.FUNCTION_KR IS 'Hideout 효과 한글';
COMMENT ON COLUMN TKL_HIDEOUT.UPGRADE_TIME IS 'Hideout 건설 시간';
COMMENT ON COLUMN TKL_HIDEOUT.UPDATE_TIME IS 'Hideout 업데이트 시간';

-- 무기 정보
CREATE TABLE TKL_WEAPON
(
    ID TEXT DEFAULT NEXTVAL('TKL_WEAPON') NOT NULL PRIMARY KEY,
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

-- 컨테이너 정보
CREATE TABLE TKL_CONTAINER
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    GRIDS JSONB,
    CAPACITY INTEGER,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_CONTAINER.ID IS '컨테이너 ID';
COMMENT ON COLUMN TKL_CONTAINER.NAME IS '컨테이너 이름';
COMMENT ON COLUMN TKL_CONTAINER.SHORT_NAME IS '컨테이너 짧은 이름';
COMMENT ON COLUMN TKL_CONTAINER.GRIDS IS '컨테이너 공간';
COMMENT ON COLUMN TKL_CONTAINER.CAPACITY IS '컨테이너 크기';
COMMENT ON COLUMN TKL_CONTAINER.IMAGE IS '컨테이너 이미지 경로';
COMMENT ON COLUMN TKL_CONTAINER.UPDATE_TIME IS '컨테이너 업데이트 시간';

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
COMMENT ON COLUMN TKL_MEDICAL.UPDATE_TIME IS 'Medical 업데이트 시간';

-- head wear 정보
CREATE TABLE TKL_HEAD_WEAR
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    CLASS_VALUE INTEGER,
    AREAS_EN TEXT[],
    AREAS_KR TEXT[],
    DURABILITY INTEGER,
    RICOCHET_CHANCE NUMERIC(10, 4),
    WEIGHT NUMERIC(10, 4),
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HEAD_WEAR.ID IS 'HeadWear 자동 생성 ID';
COMMENT ON COLUMN TKL_HEAD_WEAR.NAME IS 'HeadWear 이름';
COMMENT ON COLUMN TKL_HEAD_WEAR.SHORT_NAME IS 'HeadWear 짧은 이름';
COMMENT ON COLUMN TKL_HEAD_WEAR.AREAS_EN IS 'HeadWear 보호 부위 한글';
COMMENT ON COLUMN TKL_HEAD_WEAR.AREAS_KR IS 'HeadWear 보호 부위 영문';
COMMENT ON COLUMN TKL_HEAD_WEAR.DURABILITY IS 'HeadWear 내구도';
COMMENT ON COLUMN TKL_HEAD_WEAR.RICOCHET_CHANCE IS 'HeadWear 도탄 확률';
COMMENT ON COLUMN TKL_HEAD_WEAR.CLASS_VALUE IS 'HeadWear 클래스';
COMMENT ON COLUMN TKL_HEAD_WEAR.WEIGHT IS 'HeadWear 무게';
COMMENT ON COLUMN TKL_HEAD_WEAR.IMAGE IS 'HeadWear 이미지 경로';
COMMENT ON COLUMN TKL_HEAD_WEAR.UPDATE_TIME IS 'HeadWear 업데이트 시간';

-- HeadPhone 정보
CREATE TABLE TKL_HEAD_PHONE
(
    ID TEXT NOT NULL PRIMARY KEY,
    NAME TEXT,
    SHORT_NAME TEXT,
    IMAGE TEXT,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_HEAD_PHONE.ID IS 'HeadPhone ID';
COMMENT ON COLUMN TKL_HEAD_PHONE.NAME IS 'HeadPhone 이름';
COMMENT ON COLUMN TKL_HEAD_PHONE.SHORT_NAME IS 'HeadPhone 짧은 이름';
COMMENT ON COLUMN TKL_HEAD_PHONE.IMAGE IS 'HeadPhone 이미지 경로';
COMMENT ON COLUMN TKL_HEAD_PHONE.UPDATE_TIME IS 'HeadPhone 업데이트 시간';

-- 총알 정보
CREATE SEQUENCE SEQ_TKL_AMMO START 1;
CREATE TABLE TKL_AMMO
(
    ID INTEGER DEFAULT NEXTVAL('SEQ_TKL_AMMO') NOT NULL PRIMARY KEY,
    NAME VARCHAR(80) NOT NULL,
    CALIBER VARCHAR(50) NOT NULL,
    DAMAGE INTEGER NOT NULL,
    PENETRATION_POWER INTEGER NOT NULL,
    DAMAGE_PERCENT INTEGER NOT NULL,
    RECOIL INTEGER NOT NULL,
    FRAG_CHANCE INTEGER NOT NULL,
    LIGHT_BLEED INTEGER NOT NULL,
    HEAVY_BLEED INTEGER NOT NULL,
    SPEED INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_FIRST INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_SECOND INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_THIRD INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_FOURTH INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_FIFTH INTEGER NOT NULL,
    BULLET_EFFECTIVENESS_SIXTH INTEGER NOT NULL,
    USED_BY JSONB NOT NULL,
    IMAGE TEXT NOT NULL,
    UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_AMMO.ID IS 'Ammo 자동 생성 ID';
COMMENT ON COLUMN TKL_AMMO.NAME IS 'Ammo 이름';
COMMENT ON COLUMN TKL_AMMO.CALIBER IS 'Ammo 구경';
COMMENT ON COLUMN TKL_AMMO.DAMAGE IS 'Ammo 데미지';
COMMENT ON COLUMN TKL_AMMO.PENETRATION_POWER IS 'Ammo 관통력';
COMMENT ON COLUMN TKL_AMMO.DAMAGE_PERCENT IS 'Ammo 데미지 비율';
COMMENT ON COLUMN TKL_AMMO.RECOIL IS 'Ammo 반동';
COMMENT ON COLUMN TKL_AMMO.FRAG_CHANCE IS 'Ammo 적을 제거할 확률';
COMMENT ON COLUMN TKL_AMMO.LIGHT_BLEED IS 'Ammo 빛 양';
COMMENT ON COLUMN TKL_AMMO.HEAVY_BLEED IS 'Ammo 출혈량';
COMMENT ON COLUMN TKL_AMMO.SPEED IS 'Ammo 총알 속도';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_FIRST IS 'Ammo 1갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_SECOND IS 'Ammo 2갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_THIRD IS 'Ammo 3갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_FOURTH IS 'Ammo 4갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_FIFTH IS 'Ammo 5갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.BULLET_EFFECTIVENESS_SIXTH IS 'Ammo 6갑옷 관통 효율';
COMMENT ON COLUMN TKL_AMMO.USED_BY IS 'Ammo 사용하는 총';
COMMENT ON COLUMN TKL_AMMO.IMAGE IS 'Ammo 이미지 경로';
COMMENT ON COLUMN TKL_AMMO.UPDATE_TIME IS 'Ammo 업데이트 시간';

-- main menu 정보
CREATE TABLE TKL_MAIN_MENU
(
  VALUE VARCHAR(40) NOT NULL PRIMARY KEY,
  EN_NAME VARCHAR(40) NOT NULL,
  KR_NAME VARCHAR(40) NOT NULL,
  LINK VARCHAR(60),
  ORDER INTEGER NOT NULL,
  IMAGE VARCHAR(60),
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAIN_MENU.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_MAIN_MENU.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_MAIN_MENU.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_MAIN_MENU.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_MAIN_MENU.ORDER IS 'Menu 순서';
COMMENT ON COLUMN TKL_MAIN_MENU.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_MAIN_MENU.UPDATE_TIME IS 'Menu 업데이트 시간';

-- sub menu 정보
CREATE TABLE TKL_SUB_MENU
(
  VALUE VARCHAR(40) NOT NULL PRIMARY KEY,
  EN_NAME VARCHAR(40) NOT NULL,
  KR_NAME VARCHAR(40) NOT NULL,
  PARENT_VALUE VARCHAR(40) NOT NULL,
  LINK VARCHAR(60),
  ORDER INTEGER NOT NULL,
  IMAGE VARCHAR(60),
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_SUB_MENU.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_SUB_MENU.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_SUB_MENU.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_SUB_MENU.PARENT_VALUE IS 'Menu 상위 값';
COMMENT ON COLUMN TKL_SUB_MENU.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_SUB_MENU.ORDER IS 'Menu 순서';
COMMENT ON COLUMN TKL_SUB_MENU.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_SUB_MENU.UPDATE_TIME IS 'Menu 업데이트 시간';

-- main info
CREATE TABLE TKL_MAIN
(
  VALUE VARCHAR(40) NOT NULL PRIMARY KEY,
  EN_NAME VARCHAR(40) NOT NULL,
  KR_NAME VARCHAR(40) NOT NULL,
  LINK VARCHAR(60),
  ORDER INTEGER NOT NULL,
  IMAGE VARCHAR(60),
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_MAIN.VALUE IS 'Menu 값';
COMMENT ON COLUMN TKL_MAIN.EN_NAME IS 'Menu 이름 영문';
COMMENT ON COLUMN TKL_MAIN.KR_NAME IS 'Menu 이름 한글';
COMMENT ON COLUMN TKL_MAIN.LINK IS 'Menu 주소';
COMMENT ON COLUMN TKL_MAIN.ORDER IS 'Menu 순서';
COMMENT ON COLUMN TKL_MAIN.IMAGE IS 'Menu 이미지';
COMMENT ON COLUMN TKL_MAIN.UPDATE_TIME IS 'Menu 업데이트 시간';
        
-- table_column 정보
CREATE TABLE TKL_TABLE_COLUMN
(
  ID VARCHAR(40) NOT NULL PRIMARY KEY,
  VALUE_KR TEXT[],
  VALUE_EN TEXT[],
  JSON_VALUE jsonb,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_TABLE_COLUMN.ID IS 'Column 아이디';
COMMENT ON COLUMN TKL_TABLE_COLUMN.VALUE_KR IS 'Column 값 영문';
COMMENT ON COLUMN TKL_TABLE_COLUMN.VALUE_EN IS 'Column 값 한글';
COMMENT ON COLUMN TKL_TABLE_COLUMN.JSON_VALUE IS 'Column json 데이터';
COMMENT ON COLUMN TKL_TABLE_COLUMN.UPDATE_TIME IS 'Column 업데이트 시간';

-- 탈출구 정보
CREATE TABLE TKL_EXTRACTION
(
  ID VARCHAR(40) NOT NULL PRIMARY KEY,
  NAME TEXT,
  IMAGE TEXT,
  FACTION VARCHAR(20),
  ALWAYS_AVAILABLE BOOLEAN,
  SINGLE_USE BOOLEAN,
  REQUIREMENTS jsonb,
  TIP TEXT[],
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
COMMENT ON COLUMN TKL_EXTRACTION.UPDATE_TIME IS '탈출구 업데이트 시간';

-- 검색 정보
CREATE TABLE TKL_SEARCH
(
  ID VARCHAR(40) NOT NULL PRIMARY KEY,
  VALUE VARCHAR(60),
  LINK TEXT,
  ORDER INTEGER,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_SEARCH.ID IS '검색 아이디';
COMMENT ON COLUMN TKL_SEARCH.VALUE IS '검색 드롭다운 표시 값';
COMMENT ON COLUMN TKL_SEARCH.LINK IS '검색 연동 링크';
COMMENT ON COLUMN TKL_SEARCH.ORDER IS '검색 순서';
COMMENT ON COLUMN TKL_SEARCH.UPDATE_TIME IS '검색 업데이트 시간';

-- Item Filter Categories
CREATE TABLE TKL_FILTER_CATEGORIES (
    VALUE VARCHAR(255) NOT NULL PRIMARY KEY,
    EN VARCHAR(255) NOT NULL,
    KR VARCHAR(255) NOT NULL,
    FILTER_UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.VALUE IS 'Filter 값';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.EN IS 'Filter 영문';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.KR IS 'Filter 한글';
COMMENT ON COLUMN TKL_FILTER_CATEGORIES.FILTER_UPDATE_TIME IS 'Filter 업데이트 시간';

-- Item Filter SubCategories
CREATE TABLE TKL_FILTER_SUB_CATEGORIES (
    VALUE VARCHAR(255) NOT NULL PRIMARY KEY,
    EN VARCHAR(255) NOT NULL,
    KR VARCHAR(255) NOT NULL,
    FILTER_PARENT_VALUE VARCHAR(255) NOT NULL,
    FILTER_SUB_UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.VALUE IS 'Filter Sub 값';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.EN IS 'Filter Sub 영문';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.KR IS 'Filter Sub 한글';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.FILTER_PARENT_VALUE IS 'Filter Sub 상위 키';
COMMENT ON COLUMN TKL_FILTER_SUB_CATEGORIES.FILTER_SUB_UPDATE_TIME IS 'Filter Sub 업데이트 시간';

-- food and drink
CREATE TABLE TKL_FOOD_DRINK
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
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_FOOD_DRINK.ID IS '음식 아이디';
COMMENT ON COLUMN TKL_FOOD_DRINK.NAME_EN IS '음식 영문';
COMMENT ON COLUMN TKL_FOOD_DRINK.NAME_KR IS '음식 한글';
COMMENT ON COLUMN TKL_FOOD_DRINK.SHORT_NAME IS '음식 짧은 이름';
COMMENT ON COLUMN TKL_FOOD_DRINK.CATEGORY IS '음식 카테고리';
COMMENT ON COLUMN TKL_FOOD_DRINK.ENERGY IS '음식 에너지';
COMMENT ON COLUMN TKL_FOOD_DRINK.HYDRATION IS '음식 수분';
COMMENT ON COLUMN TKL_FOOD_DRINK.IMAGE IS '음식 이미지';
COMMENT ON COLUMN TKL_FOOD_DRINK.STIM_EFFECTS IS '음식 효과';
COMMENT ON COLUMN TKL_FOOD_DRINK.UPDATE_TIME IS '음식 업데이트 시간';

-- ammo
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
COMMENT ON COLUMN TKL_AMMO.ID IS '총알 아이디';
COMMENT ON COLUMN TKL_AMMO.NAME IS '총알 영문';
COMMENT ON COLUMN TKL_AMMO.SHORT_NAME IS '총알 영문';
COMMENT ON COLUMN TKL_AMMO.CATEGORY IS '총알 카테고리';
COMMENT ON COLUMN TKL_AMMO.ROUND IS '총알 탄약';
COMMENT ON COLUMN TKL_AMMO.DAMAGE IS '총알 데미지';
COMMENT ON COLUMN TKL_AMMO.PENETRATION_POWER IS '총알 관통력';
COMMENT ON COLUMN TKL_AMMO.ARMOR_DAMAGE IS '총알 방어구 피해량';
COMMENT ON COLUMN TKL_AMMO.ACCURACY_MODIFIER IS '총알 정확성';
COMMENT ON COLUMN TKL_AMMO.RECOIL_MODIFIER IS '총알 반동';
COMMENT ON COLUMN TKL_AMMO.LIGHT_BLEED_MODIFIER IS '총알 가벼운 출혈';
COMMENT ON COLUMN TKL_AMMO.HEAVY_BLEED_MODIFIER IS '총알 깊은 출혈';
COMMENT ON COLUMN TKL_AMMO.EFFICIENCY IS '총알 방어 등급 효율성';
COMMENT ON COLUMN TKL_AMMO.IMAGE IS '총알 사진';
COMMENT ON COLUMN TKL_AMMO.UPDATE_TIME IS '총알 업데이트 시간';


-- 전리품 정보
CREATE TABLE TKL_LOOT
(
  ID TEXT NOT NULL PRIMARY KEY,
  NAME TEXT,
  SHORT_NAME TEXT,
  IMAGE TEXT,
  NOTES JSONB,
  CATEGORY TEXT,
  UPDATE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN TKL_LOOT.ID IS '전리품 아이디';
COMMENT ON COLUMN TKL_LOOT.NAME IS '전리품 이름';
COMMENT ON COLUMN TKL_LOOT.SHORT_NAME IS '전리품 짧은 이름';
COMMENT ON COLUMN TKL_LOOT.IMAGE IS '전리품 사진';
COMMENT ON COLUMN TKL_LOOT.NOTES IS '전리품 연관 정보 - 퀘스트, 하이드 아웃';
COMMENT ON COLUMN TKL_LOOT.CATEGORY IS '전리품 카테고리';
COMMENT ON COLUMN TKL_LOOT.UPDATE_TIME IS '전리품 업데이트 시간';