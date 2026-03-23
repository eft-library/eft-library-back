- [타르코프 도서관의 운영 방식](#타르코프-도서관의-운영-방식)
  * [주요 사항](#주요-사항)
  * [환경 및 패키지 정보](#환경-및-패키지-정보)
  * [구조](#구조)
  * [개발 History](#개발-history)


# 타르코프 도서관의 운영 방식

EFT Library Backend는 FastAPI를 사용하여 구축하였고, PostgreSQL의 데이터를 적재하거나 조회합니다.

<img width="1314" height="1275" alt="arch_v4" src="https://github.com/user-attachments/assets/0392b55e-14b0-45d8-9aa6-4b83a9cd640f" />

## 주요 사항

- 회원가입과 로그인의 경우 **NextJS의 next-auth를 사용**하고, Google에서 발급한 token을 FastAPI로 전달한 뒤, **FastAPI에서 Google의 Token 유효성 검사 통신을 통해 인증 및 인가**를 진행합니다.
- 회원가입은 무조건 Google OAuth를 사용하고, **사용자 이메일 정보만 사용합니다. (비밀번호 사용 X)**
- Middleware를 추가하여, 모든 요청을 Kafka를 통해 History를 남깁니다.
- 가능하면 모든 데이터의 가공을 FastAPI에서 처리합니다.
- WebSocket과 Redis를 사용하여 실시간 알림 기능을 제공합니다.
- 별도로 구축한 LLM Server에 MCP API 통신을 사용하여 AI Agent Chat 사용하고 있습니다.


## 패키지 정보

| 패키지명            | 버전      | 선정 이유                                     |
|-----------------|---------|-------------------------------------------|
| Python          | 3.12.11 | 최신 문법 및 성능 개선                             |
| FastAPI         | 0.124.0 | 고성능 비동기 API 프레임워크                         |
| psycopg2-binary | 2.9.11  | PostgreSQL 안정적 드라이버                       |
| python-dotenv   | 1.1.0   | 환경 변수 관리                                  |
| pytz            | 2025.2  | 타임존 처리                                    |
| requests        | 2.32.5  | 간단한 HTTP 요청 처리                            |
| SQLAlchemy      | 2.0.44  | ORM 기반 DB 추상화                             |
| confluent-kafka | 2.12.2  | Kafka 메시지 처리                              |
| minio           | 7.2.20  | S3 호환 객체 스토리지, 이미지 저장 용도                  |
| nanoid          | 2.0.0   | 짧고 고유한 ID 생성, 댓글 아이디 생성                   |
| pillow          | 12.0.0  | 이미지 처리, webp로 압축 후 minio 저장               |
| python-slugify  | 8.0.4   | URL 친화적 문자열 생성, 게시판 생성시 제목을 url로 변환할 때 사용 |
| redis           | 7.1.0   | 캐시 및 빠른 데이터 저장소, 사용자 알림과 외부 프로그램 연동에 사용   |




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
  - **community** : 커뮤니티 관련 API
  - **comment** : 댓글 관련 API
  - **chat** : MCP AI Agent 관련 API
  - **minigame** : 웹게임 API
- **util**
  - **constants** : HTTP Code 정의
  - **kafka_producer** : Kafka 메시지 처리
  - **middleware** : HTTP 요청 중단 처리
  - **snowflake** : 서버 정보 기단 snowflake id 생성 - 게시판 아이디에 사용
  - **websocket** : Websocket 처리
- **database** : PostgreSQL Connection 정의
- **DB.sql** : PostgreSQL Table 정의
- **Vector.sql** : Rag Document Table 정의

## 개발 History

여기에서 확인해 주세요!

[velog 바로가기](https://velog.io/@poeynus/series/%EB%B0%B1%EC%97%94%EB%93%9C-%EA%B0%9C%EB%B0%9C)

<!--
pip install 'fastapi[all]' sqlalchemy python-dotenv psycopg2-binary requests pytz confluent-kafka tzdata redis python-slugify pillow minio nanoid setuptools
-->
