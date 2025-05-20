- [EFT Library의 Backend 운영 방식](#eft-library의-backend-운영-방식)
  * [주요 사항](#주요-사항)
  * [환경 및 패키지 정보](#환경-및-패키지-정보)
  * [구조](#구조)
  * [운영 중 발생한 문제 및 해결 과정](#운영-중-발생한-문제-및-해결-과정)
    + [1. SQLAlchemy ORM 적용](#1-sqlalchemy-orm-적용)
    + [2. 너무 복잡한 쿼리의 경우](#2-너무-복잡한-쿼리의-경우)
    + [3. 하위 항목 전체 조회](#3-하위-항목-전체-조회)
    + [4. 다국어 지원](#4-다국어-지원)

# EFT Library의 Backend 운영 방식

EFT Library Backend는 FastAPI를 사용하여 구축하였고, PostgreSQL의 데이터를 적재하거나 조회한다.

이 페이지는 Backend에 대하여 설명한다.

![architecture](https://github.com/user-attachments/assets/97befe41-42a4-4165-b673-83f8fe947a20)



## 주요 사항

- 회원가입과 로그인의 경우 **NextJS의 next-auth를 사용**하고, Google에서 발급한 token을 FastAPI로 전달한 뒤, **FastAPI에서 Google의 Token 유효성 검사 통신을 통해 인증 및 인가**를 진행한다.
- 회원가입은 무조건 Google OAuth를 사용하고, **사용자 이메일 정보만 사용한다. (비밀번호 사용 X)**
- 가능한 경우 SQLAlchmey의 ORM을 사용한다.
- Middleware를 추가하여, 모든 요청을 Kafka를 통해 History를 남긴다.
- 가능하면 모든 데이터의 가공을 FastAPI에서 처리한다.


## 환경 및 패키지 정보

- Ubuntu 22.04.5 LTS
- RAM DDR4 32GB
- CPU Ryzen 5 3600, 6 core / 12 thread
- Python 3.10.12
- FastAPI 0.115.12
- psycopg2-binary 2.9.10
- python-dotenv 1.1.0
- pytz 2025.2
- requests 2.32.3
- SQLAlchemy 2.0.40
- confluent-kafka 2.10.0

## 구조

- **api**
  - **boss** : 보스 API
  - **item** : 모든 아이템 API
  - **item filter** : 대화형 지도에서 사용하는 아이템 필터링 API
  - **map** : 대화형 지도 API
  - **map of tarkov** : 타르코프 지도 API
  - **menu** : 메인 페이지 아이템 및 Nav 아이템 API
  - **news** : 타르코프 초기화 관련 API
  - **notice** : 사이트 공지 API
  - **patch notes** : 타르코프 패치 노트 API
  - **event** : 타르코프 이벤트 정보 API
  - **hideout** : 사용자 상호작용 은신처 API
  - **quest** : Quest API
  - **planner** : 사용자 상호작용 Quest Planner API
  - **roadmap** : 사용자 상호작용 Quest Roadmap API
  - **search** : 메인 페이지 검색 및 sitemap.xml 조회 API
  - **dynamic info** : 사이트 내의 상수 조회 API - footer, etc...
  - **user** : 사용자 관련 API
- **util**
  - **constants** : HTTP Code 정의
- **database** : PostgreSQL Connection 정의
- **kafka_producer** : Middleware에서 받은 사용자 페이지 요청 정보를 Kafka로 전달하는 서비스
- **DB.sql** : PostgreSQL Table 정의


## 운영 중 발생한 문제 및 해결 과정

### 1. SQLAlchemy ORM 적용

FastAPI를 사용하면서 하는김에 해보자! 로 시작했는데, 어려웠다...
특히 처음에 DB와 Connection을 만들어서 조회 후 반환을 하는데, 계속 빈 값만 나오는 문제가 있었는데, SQLAlchemy의 Session이 끝난 뒤 값을 반환해서 생기는 문제였다. 

#### 이전
<img width="590" alt="3" src="https://github.com/user-attachments/assets/b0902073-41f2-429b-b693-8ec91b80bf2a" />

#### 수정
<img width="490" alt="4" src="https://github.com/user-attachments/assets/fcbaecd9-38e6-4595-b0ee-1df9cb28b35d" />


**✔ 해결:**  
- Database Connection 코드 수정 및 새로운 로직으로 변경

#### 이전
![1](https://github.com/user-attachments/assets/5db35002-af3c-480c-b328-bdd755f463a8)

#### 수정
![2](https://github.com/user-attachments/assets/a8a05856-ba29-4ffb-a0ce-48872942654a)


### 2. 너무 복잡한 쿼리의 경우

어떻게든 ORM을 사용하여 해결해보려 했는데, 구조가 점점 복잡해지면서 유지보수에 한계가 생길 것 같아 text, execute 방식으로 우회 하였다.

![스크린샷 2025-05-21 오전 8 17 50](https://github.com/user-attachments/assets/533576f2-63e0-4c09-b49e-962769116f0d)


**✔ 해결:**  
- ORM을 사용하지 않고 Query 직접 작성하였다.
```python

@staticmethod
def get_item_detail_query():
"""
아이템 상세 정보 조회 쿼리
"""

return """
WITH target_item AS (SELECT *
                     FROM item_i18n
                     WHERE url_mapping = :url_mapping
                     limit 1),

     -- 📦 바터 정보
     filtered_barters AS (SELECT n.id                      AS npc_id,
                                 n.name,
                                 n.image,
                                 jsonb_build_object(
                                         'level', barter ->> 'level',
                                         'rewardItems', reward,
                                         'requiredItems', barter -> 'requiredItems'
                                 )                         AS matching_barter,
                                 reward -> 'item' ->> 'id' AS reward_item_id
                          FROM npc_i18n n,
                               jsonb_array_elements(n.barter_info) AS barter,
                               jsonb_array_elements(barter -> 'rewardItems') AS reward),

     -- 🛠 은신처 건설에 사용되는 정보
     filtered_hideout AS (SELECT thir.id,
                                 thir.level_id,
                                 thir.name,
                                 thir.quantity,
                                 thir.count,
                                 thir.image,
                                 thir.item_id,
                                 thm.name as master_name,
                                 thm.id   as master_id
                          FROM hideout_item_require_i18n thir
                                   LEFT JOIN hideout_master_i18n thm
                                             ON SPLIT_PART(thir.level_id, '-', 1) = thm.id),

     -- 🛠 은신처 제작에 사용되는 정보
     filtered_crafts AS (SELECT DISTINCT ON (thc.id) thc.*,
                                                     thm.name                as master_name,
                                                     thm.id                  as master_id,
                                                     elem -> 'item' ->> 'id' AS required_item_id
                         FROM hideout_crafts_i18n thc
                                  LEFT JOIN LATERAL jsonb_array_elements(thc.req_item) AS elem on True
                                  LEFT JOIN hideout_master_i18n thm ON SPLIT_PART(thc.level_id, '-', 1) = thm.id),

     -- 🎯 퀘스트 보상으로 사용되는 정보
     filtered_quests AS (SELECT distinct on (qa.id) qa.id                                           AS quest_id,
                                                    qa.name,
                                                    qa.npc_id,
                                                    qa.url_mapping,
                                                    tn.name                                         as npc_name,
                                                    tn.image                                        AS npc_image,
                                                    jsonb_array_elements(finish_rewards -> 'items') AS reward_elem
                         FROM quest_i18n qa
                                  left join npc_i18n tn on qa.npc_id = tn.id
                         WHERE qa.name is not null),

     -- ❗ questItem에 포함된 경우 (예: giveQuestItem, findQuestItem)
     required_quests_by_quest_item AS (SELECT DISTINCT ON (q.id) q.id     AS quest_id,
                                                                 q.name,
                                                                 q.url_mapping,
                                                                 tn.name  AS npc_name,
                                                                 tn.image AS npc_image,
                                                                 obj      AS objective
                                       FROM quest_i18n q
                                                LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS obj ON TRUE
                                                LEFT JOIN npc_i18n tn ON q.npc_id = tn.id
                                       WHERE obj ->> 'type' IN ('findQuestItem', 'giveQuestItem')
                                         AND q.name IS NOT NULL),

     -- ❗ items 배열에 포함된 경우 (예: giveItem, plantItem, findItem)
     required_quests_by_items_array AS (SELECT distinct on (q.id) q.id     AS quest_id,
                                                                  q.name,
                                                                  q.url_mapping,
                                                                  tn.name  as npc_name,
                                                                  tn.image AS npc_image,
                                                                  obj      AS objective
                                        FROM quest_i18n q
                                                 LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS obj ON TRUE
                                                 LEFT JOIN npc_i18n tn on q.npc_id = tn.id
                                        WHERE obj ->> 'type' IN ('plantItem', 'giveItem', 'findItem')
                                          AND q.name is not null
                                          AND EXISTS (SELECT 1
                                                      FROM jsonb_array_elements(obj -> 'items') AS item
                                                      WHERE item ->> 'id' = (SELECT id FROM target_item))),

     item_with_details AS (SELECT ti.id,
                                  ti.name,
                                  ti.category,
                                  ti.image,
                                  ti.image_width,
                                  ti.image_height,
                                  ti.info,
                                  ti.update_time,
                                  ti.url_mapping,

                                  -- 은신처 아이템 요구 정보
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'id', thir.id,
                                                          'level_id', thir.level_id,
                                                          'name', thir.name,
                                                          'quantity', thir.quantity,
                                                          'count', thir.count,
                                                          'image', thir.image,
                                                          'item_id', thir.item_id,
                                                          'master_name', thir.master_name,
                                                          'master_id', thir.master_id
                                                           )
                                                          ) FILTER (WHERE thir.id IS NOT NULL),
                                                  '[]'
                                  ) AS hideout_items,

                                  -- 은신처 제작에 사용
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'id', thc.id,
                                                          'name', thc.name,
                                                          'level_id', thc.level_id,
                                                          'level', thc.level,
                                                          'duration', thc.duration,
                                                          'req_item', thc.req_item,
                                                          'reward_item_id', thc.reward_item_id,
                                                          'image', thc.image,
                                                          'quantity', thc.quantity,
                                                          'master_name', thc.master_name,
                                                          'master_id', thc.master_id
                                                           )
                                                          ) FILTER (WHERE thc.id IS NOT NULL),
                                                  '[]'
                                  ) AS used_in_crafts,

                                  -- NPC 바터 보상으로 나오는 정보
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'npc_id', fb.npc_id,
                                                          'npc_image', fb.image,
                                                          'npc_name', fb.name,
                                                          'barter_info', fb.matching_barter
                                                           )
                                                          ) FILTER (WHERE fb.npc_id IS NOT NULL),
                                                  '[]'
                                  ) AS rewarded_by_npcs,

                                  -- 퀘스트 보상으로 나오는 정보
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'quest_id', fq.quest_id,
                                                          'name', fq.name,
                                                          'npc_name', fq.npc_name,
                                                          'npc_image', fq.npc_image,
                                                          'url_mapping', fq.url_mapping,
                                                          'reward', fq.reward_elem
                                                           )
                                                          ) FILTER (WHERE fq.quest_id IS NOT NULL),
                                                  '[]'
                                  ) AS rewarded_by_quests,

                                  -- 📌 questItem에 들어 있는 퀘스트
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'quest_id', rqi.quest_id,
                                                          'name', rqi.name,
                                                          'npc_name', rqi.npc_name,
                                                          'npc_image', rqi.npc_image,
                                                          'url_mapping', rqi.url_mapping,
                                                          'objective', rqi.objective
                                                           )
                                                          ) FILTER (
                                                      WHERE rqi.objective -> 'questItem' ->> 'id' = ti.id
                                                      ),
                                                  '[]'
                                  ) AS required_by_quest_item,

                                  -- 📌 items 배열에 들어 있는 퀘스트
                                  COALESCE(
                                                  json_agg(
                                                  DISTINCT jsonb_build_object(
                                                          'quest_id', rqa.quest_id,
                                                          'name', rqa.name,
                                                          'npc_name', rqa.npc_name,
                                                          'npc_image', rqa.npc_image,
                                                          'url_mapping', rqa.url_mapping,
                                                          'objective', rqa.objective
                                                           )
                                                          ) FILTER (WHERE rqa.quest_id IS NOT NULL),
                                                  '[]'
                                  ) AS required_by_quest_item_array

                           FROM target_item ti
                                    LEFT JOIN filtered_hideout thir ON ti.id = thir.item_id
                                    LEFT JOIN filtered_crafts thc ON thc.required_item_id = ti.id
                                    LEFT JOIN filtered_barters fb ON fb.reward_item_id = ti.id
                                    LEFT JOIN filtered_quests fq ON fq.reward_elem -> 'item' ->> 'id' = ti.id
                                    LEFT JOIN required_quests_by_quest_item rqi
                                              ON rqi.objective -> 'questItem' ->> 'id' = ti.id
                                    LEFT JOIN required_quests_by_items_array rqa ON TRUE
                           GROUP BY ti.id, ti.name, ti.name, ti.category, ti.image,
                                    ti.image_width, ti.image_height, ti.info, ti.update_time, ti.url_mapping)

SELECT *
FROM item_with_details
"""
```

### 3. 하위 항목 전체 조회

ORM을 사용하면 ForeignKey와 relationship을 가지고 하위 항목을 전체 조회 해서 자동으로 배열로 넣어주는데, 처음에 몰라서 많이 헤멨었다.

조회하면서 정렬도 적용할 수 있고 꽤나 편한 요소인데, 쿼리가 복잡해지면 내 입장에서는 좀 꼬이는 부분이 많아서 이런 경우는 Query를 직접 작성하고 가공했었다.

![스크린샷 2025-05-21 오전 8 24 56](https://github.com/user-attachments/assets/9bf67cb4-8fe0-44b2-a9f7-97cb1a2a25b2)


### 4. 다국어 지원

기존에는 name_en, name_kr 식으로 컬럼을 지정해줬었는데, jsonb로 컬럼을 수정하고 하나로 합쳤다.

name: {en: test, ko: 테스트, テスト }

이렇게 바꾸면서 모든 테이블을 갈아엎고 새로 만들었다.


<!--
pip install 'fastapi[all]'
pip install sqlalchemy
pip install python-dotenv
pip install psycopg2-binary
pip install requests
pip install pytz
pip install confluent-kafka
uvicorn main:app --reload 
-->
