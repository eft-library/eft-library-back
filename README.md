# EFT Library의 Backend 운영 방식

EFT Library Backend는 FastAPI를 사용하여 구축하였고, PostgreSQL의 데이터를 적재하거나 조회한다.

이 페이지는 Backend에 대하여 설명한다.

![back](https://github.com/user-attachments/assets/9c4a7e00-8d10-4de7-b256-37e2b2e41834)



## 주요 사항

- 회원가입과 로그인의 경우 **NextJS의 next-auth를 사용**하는데, Google에서 발급한 token을 FastAPI로 전달한 뒤, **FastAPI에서 Google의 Token 유효성 검사 통신을 통해 인증 및 인가**를 진행한다.
- 회원가입은 무조건 Google OAuth를 사용하고, **사용자 이메일 정보만 사용한다. (비밀번호 사용 X)**
- 가능한 경우 SQLAlchmey의 ORM을 사용한다.
- 가능하면 모든 데이터의 가공을 FastAPI에서 처리한다.


## 환경

- Rocky Linux 8
- Python 3.6
- FastAPI 0.83.0
- psycopg2-binary 2.9.5
- python-dotenv 0.20.0
- pytz 2024.1
- requests 2.27.1
- SQLAlchemy 1.4.52

## 구조

- **api**
  - **boss** : 보스 API
  - **event** : 타르코프 이벤트 정보 API
  - **item** : 모든 아이템 API
  - **item filter** : 대화형 지도에서 사용하는 아이템 필터링 API
  - **map** : 대화형 지도 API
  - **map of tarkov** : 타르코프 지도 API
  - **menu** : 메인 페이지 아이템 및 Nav 아이템 API
  - **news** : 메인 페이지 News API
  - **notice** : 사이트 공지 API
  - **patch notes** : 타르코프 패치 노트 API
  - **quest** : Quest 관련 API
  - **roadmap** : 사용자 상호작용 퀘스트 Roadmap API
  - **search** : 메인 페이지 검색 및 sitemap.xml 조회 API
  - **server** : 웹 Reboot 관련 API
  - **table column** : 사이트 내의 상수 조회 API
  - **user** : 사용자 관련 API
- **util**
  - **constants** : HTTP Code 정의
- **database** : PostgreSQL Connection 정의
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

![스크린샷 2025-01-31 오후 3 35 24](https://github.com/user-attachments/assets/ecb540c6-9826-48d0-b04f-954ea5a040a5)


**✔ 해결:**  
- ORM을 사용하지 않고 Query 직접 작성
```python

@staticmethod
def get_hideout_query():
"""
하이드 아웃 전체 조회 쿼리
"""

return """
SELECT master_id,
       master_name_en,
       master_name_kr,
       image,
       json_agg(
               jsonb_build_object(
                       'level_id', level_id,
                       'item_require', item_require,
                       'level_info', level_info,
                       'trader_require', trader_require,
                       'station_require', station_require,
                       'skill_require', skill_require,
                       'bonus', bonus,
                       'crafts', crafts
               )
       ) as data
FROM (SELECT tkl_hideout_master.id as master_id,
             tkl_hideout_master.name_en as master_name_en,
             tkl_hideout_master.name_kr as master_name_kr,
             lid as level_id,
             tkl_hideout_master.image as image,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'id', tkl_hideout_item_require.id,
                                     'name_en', tkl_hideout_item_require.name_en,
                                     'name_kr', tkl_hideout_item_require.name_kr,
                                     'count', tkl_hideout_item_require.count,
                                     'quantity', tkl_hideout_item_require.quantity,
                                     'image', tkl_hideout_item_require.image
                                      )
                                     )
                             FILTER (WHERE tkl_hideout_item_require.id IS NOT NULL),
                             '[]'::json) as item_require,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'level', tkl_hideout_level.level,
                                     'construction_time', tkl_hideout_level.construction_time
                                      )
                                     ) FILTER (WHERE tkl_hideout_level.level IS NOT NULL),
                             '[]'::json) as level_info,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'name_en', tkl_hideout_trader_require.name_en,
                                     'name_kr', tkl_hideout_trader_require.name_kr,
                                     'compare', tkl_hideout_trader_require.compare,
                                     'require_type', tkl_hideout_trader_require.require_type,
                                     'value', tkl_hideout_trader_require.value,
                                     'image', tkl_hideout_trader_require.image
                                      )
                                     ) FILTER (WHERE tkl_hideout_trader_require.name_en IS NOT NULL),
                             '[]'::json) as trader_require,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'level', tkl_hideout_station_require.level,
                                     'name_en', tkl_hideout_station_require.name_en,
                                     'name_kr', tkl_hideout_station_require.name_kr,
                                     'image', tkl_hideout_station_require.image
                                      )
                                     ) FILTER (WHERE tkl_hideout_station_require.level IS NOT NULL),
                             '[]'::json) as station_require,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'level', tkl_hideout_skill_require.level,
                                     'name_en', tkl_hideout_skill_require.name_en,
                                     'name_kr', tkl_hideout_skill_require.name_kr,
                                     'image', tkl_hideout_skill_require.image
                                      )
                                     ) FILTER (WHERE tkl_hideout_skill_require.level IS NOT NULL),
                             '[]'::json) as skill_require,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'name_en', tkl_hideout_bonus.name_en,
                                     'name_kr', tkl_hideout_bonus.name_kr,
                                     'value', tkl_hideout_bonus.value,
                                     'skill_name_en', tkl_hideout_bonus.skill_name_en,
                                     'skill_name_kr', tkl_hideout_bonus.skill_name_kr
                                      )
                                     ) FILTER (WHERE tkl_hideout_bonus.name_en IS NOT NULL),
                             '[]'::json) as bonus,
             COALESCE(
                             json_agg(
                             distinct jsonb_build_object(
                                     'level', tkl_hideout_crafts.level,
                                     'name_en', tkl_hideout_crafts.name_en,
                                     'name_kr', tkl_hideout_crafts.name_kr
                                      )
                                     ) FILTER (WHERE tkl_hideout_crafts.level IS NOT NULL),
                             '[]'::json) as crafts
      FROM tkl_hideout_master
               LEFT JOIN LATERAL
          unnest(tkl_hideout_master.level_ids) AS lid ON true
               LEFT JOIN
           tkl_hideout_item_require ON lid = tkl_hideout_item_require.level_id
               LEFT JOIN
           tkl_hideout_level on lid = tkl_hideout_level.id
               LEFT JOIN
           tkl_hideout_trader_require on lid = tkl_hideout_trader_require.level_id
               LEFT JOIN
           tkl_hideout_station_require on lid = tkl_hideout_station_require.level_id
               LEFT JOIN
           tkl_hideout_skill_require on lid = tkl_hideout_skill_require.level_id
               LEFT JOIN
           tkl_hideout_bonus on lid = tkl_hideout_bonus.level_id
               LEFT JOIN
           tkl_hideout_crafts on lid = tkl_hideout_crafts.level_id
      GROUP BY tkl_hideout_master.id, tkl_hideout_master.name_en, tkl_hideout_master.image, lid) as a
GROUP BY master_id, master_name_en, master_name_kr, image
"""
```

### 3. 하위 항목 전체 조회

ORM을 사용하면 ForeignKey와 relationship을 가지고 하위 항목을 전체 조회 해서 자동으로 배열로 넣어주는데, 처음에 몰라서 많이 헤멨었다.

조회하면서 정렬도 적용할 수 있고 꽤나 편한 요소인데, 쿼리가 복잡해지면 내 입장에서는 좀 꼬이는 부분이 만ㅇ항서 이런 경우는 Query를 직접 작성하고 가공했었다.

![스크린샷 2025-01-31 오후 3 30 38](https://github.com/user-attachments/assets/4ee9b326-dd14-4e09-88d0-c8899ce675fc)


### FastAPI의 경우는 첫 환경 구성이 어려웠고, 개발은 쉽게 할 수 있었다.

> 다행인거지

<!--
pip install 'fastapi[all]'
pip install sqlalchemy
pip install python-dotenv
pip install psycopg2-binary
pip install requests
pip install pytz
pip install aiokafka
uvicorn main:app --reload 
-->
