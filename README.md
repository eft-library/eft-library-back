- [EFT Library의 Backend 운영 방식](#eft-library의-backend-운영-방식)
  * [주요 사항](#주요-사항)
  * [환경 및 패키지 정보](#환경-및-패키지-정보)
  * [구조](#구조)
  * [개발 History](#개발-history)

# EFT Library의 Backend 운영 방식

EFT Library Backend는 FastAPI를 사용하여 구축하였고, PostgreSQL의 데이터를 적재하거나 조회합니다.

![architecture](https://github.com/user-attachments/assets/0aad4cb2-2a18-48e1-832c-436507af67fd)



## 주요 사항

- 회원가입과 로그인의 경우 **NextJS의 next-auth를 사용**하고, Google에서 발급한 token을 FastAPI로 전달한 뒤, **FastAPI에서 Google의 Token 유효성 검사 통신을 통해 인증 및 인가**를 진행합니다.
- 회원가입은 무조건 Google OAuth를 사용하고, **사용자 이메일 정보만 사용합니다. (비밀번호 사용 X)**
- Middleware를 추가하여, 모든 요청을 Kafka를 통해 History를 남깁니다.
- 가능하면 모든 데이터의 가공을 FastAPI에서 처리합니다.


## 패키지 정보

| 패키지명            | 버전       |
|-----------------|----------|
| Python          | 3.10.12  |
| FastAPI         | 0.115.12 |
| psycopg2-binary | 2.9.10   |
| python-dotenv   | 1.1.0    |
| pytz            | 2025.2   |
| requests        | 2.32.3   |
| SQLAlchemy      | 2.0.40   |
| confluent-kafka | 2.10.0   |


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


## 개발 History

- 🌐 [다국어 지원](https://github.com/eft-library/eft-library-history/blob/main/backend/i18n_data.md)
- 🛠️ [ORM 사용 (With SqlAlchemy)](https://github.com/eft-library/eft-library-history/blob/main/backend/orm.md)
- 🔐 [Google 로그인 도입기: 사용자 피드백으로 시작된 변화](https://github.com/eft-library/eft-library-history/blob/main/backend/token_check.md)


<!--
pip install 'fastapi[all]'
pip install sqlalchemy
pip install python-dotenv
pip install psycopg2-binary
pip install requests
pip install pytz
pip install confluent-kafka
pip install tzdata
pip install aioredis
pip install python-slugify
pip install pillow
pip install minio
pip install nanoid
pip install setuptools
-->
