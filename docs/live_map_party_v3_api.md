# Live Map 파티 V3 REST API

프론트 개발은 이 문서와 [WebSocket 연동 문서](live_map_party_v3_websocket.md)를 함께 따른다.
화면 구현 순서와 JavaScript 연결 예시는 WebSocket 문서에 있다.

기본 경로: `{API_PREFIX}/live-map/v3/party`.
예: `API_PREFIX=/api`이면 `/api/live-map/v3/party/rooms`.
Swagger의 **Live Map Party V3** 태그에서 요청/응답 스키마를 확인할 수 있다.

## 인증과 실행 조건

- 방 목록만 인증 없이 조회할 수 있다.
- 나머지 API에는 `Authorization: Bearer <Google access token>`이 필요하다.
- 생성·입장은 `user_info`에 등록된 로그인 계정만 가능하다.
- `GOOGLE_TOKEN_INFO_URL`과 V3 DB 설정은 기존 설정을 사용한다.
- 시도 제한에는 `REDIS_URL`을 우선 사용하고, 없으면 기존 `REDIS_HOST`를 사용한다.
  Redis 연결 실패 시 생성·입장·비밀번호 변경은 503을 반환한다.
  나머지 변경은 DB 커밋 후 방의 WebSocket으로 갱신을 전파한다. 커밋 이후 알림만 실패하면
  REST 성공 응답을 유지하고 `X-Party-Realtime: unavailable` 헤더를 붙인다.
  연결 복구 또는 heartbeat의 전체 스냅샷으로 동기화하므로 같은 변경을 재전송하지 않는다.
- 파티 테이블은 `platform_db.sql`에 정의된 3개 테이블을 사용한다.
  애플리케이션이 테이블을 생성하거나 변경하지 않는다. 추가 패키지 설치는 필요 없다.

## API 목록

아래 경로는 기본 경로 기준이다. 생성 응답은 HTTP 201, 그 외 성공은 HTTP 200이다.

| 메서드 | 경로 | 기능 / 권한 |
| --- | --- | --- |
| GET | `/rooms` | 공개 목록, 이름 검색, 맵 필터, 페이지 조회 |
| POST | `/rooms` | 방 생성 및 생성자 자동 입장 / 로그인 |
| GET | `/rooms/{room_id}` | 방·참여자·지속 마커 스냅샷 / 입장한 참여자 |
| POST | `/rooms/{room_id}/join` | 비밀번호 입장 / 로그인 |
| POST | `/rooms/{room_id}/leave` | 퇴장 / 입장한 참여자 |
| PATCH | `/rooms/{room_id}` | 이름·비밀번호·잠금·정원 수정 / 방장 |
| DELETE | `/rooms/{room_id}` | 방 종료 / 방장 |
| PATCH | `/rooms/{room_id}/members/me` | 자신의 닉네임·색상 변경 / 입장한 참여자 |
| POST | `/rooms/{room_id}/members/{member_id}/kick` | 강퇴 / 방장 |
| POST | `/rooms/{room_id}/owner` | 방장 양도 / 방장 |
| GET | `/rooms/{room_id}/markers` | 지속 마커 목록 / 입장한 참여자 |
| POST | `/rooms/{room_id}/markers` | 지속 마커 생성 / 입장한 참여자 |
| PUT | `/rooms/{room_id}/markers/{marker_id}` | 지속 마커 교체 / 작성자 또는 방장 |
| DELETE | `/rooms/{room_id}/markers/{marker_id}?version=1` | 지속 마커 삭제 / 작성자 또는 방장 |

## 요청 예시

방 생성:

```json
{
  "name": "같이 커스텀",
  "map_id": "실제 maps.id",
  "password": "party-password",
  "nickname": "플레이어1",
  "max_members": 5
}
```

- `name`: 앞뒤 공백 제거 후 1~60자, 중복 허용.
- `map_id`: 맵 이름/normalized_name이 아닌 DB 맵 ID.
  해당 맵 또는 직속 하위 맵에 live map 층이 있어야 하며, 선택한 맵이 비활성이면 거절한다.
- `password`: 4~128자, 공백만 있는 값 금지. 앞뒤 공백을 임의로 제거하지 않는다.
- `nickname`: 선택, 앞뒤 공백 제거 후 1~30자.
  생략하면 계정 닉네임을 사용하고 없으면 `플레이어`를 사용한다.
- `max_members`: 선택, 기본 5명, 1~10명.

방 입장:

```json
{"password": "party-password", "nickname": "플레이어2"}
```

입장 중인 계정의 중복 요청은 기존 스냅샷을 반환한다. 중복 참여자를 만들지 않고,
이미 입장 중인 계정에는 비밀번호를 다시 검사하지 않는다. 이 경우에도 시도 제한은 적용된다.
퇴장 후 재입장할 때는 비밀번호를 검사하며, 기존 참여자 ID를 재사용한다.

목록 조회: `GET /rooms?search=커스텀&map_id=실제ID&limit=20&offset=0`.
검색은 대소문자를 구분하지 않는 부분 일치이고 `%`, `_`는 일반 문자로 취급한다.
`limit`은 1~100, `offset`은 0~10000이며 생성 시각 내림차순으로 정렬한다.

방 설정 수정:

```json
{"name": "새 방 이름", "is_locked": true, "max_members": 5}
```

필요한 필드만 보낸다. 빈 객체와 명시적 `null`은 거절한다.
맵 변경은 지원하지 않는다. 비밀번호 변경은 `password` 필드로 요청한다.
입장 잠금과 비밀번호 변경은 기존 참여자의 권한을 취소하지 않는다.
현재 입장 인원보다 정원을 작게 설정할 수 없다.

방장 양도: `{"member_id": "대상 참여자 UUID"}`.
내 정보 수정: `{"nickname": "정찰", "color": "#aabbcc"}`.
색상은 대문자 `#RRGGBB`로 정규화하고, 입장 중인 다른 참여자와 중복되면 409를 반환한다.

마커 생성:

```json
{
  "floor_id": "실제 live_map_floors.id",
  "x": 125.5,
  "z": -48.25,
  "marker_type": "rally",
  "label": "여기로 집결"
}
```

- 좌표는 기존 live map의 `x/z`이며 NaN·무한대는 거절한다.
- 방 맵에 속하거나 방 맵의 직속 하위 맵에 속한 층만 허용한다.
- `marker_type`: `normal`(기본), `danger`, `rally`, `target`.
- `label`: 선택, 최대 100자. 일반 텍스트로 표시한다.
- 방당 지속 마커는 최대 200개.
- PUT 수정은 생성 필드와 **현재 `version`**을 함께 보낸다.
  교체 방식이므로 `label`을 생략하면 NULL, `marker_type`을 생략하면 normal이 된다.
  성공하면 version이 1 증가한다. 삭제도 현재 version을 쿼리로 보낸다.
  버전이 다르면 409이므로 목록을 새로 받은 뒤 다시 편집한다.

## 응답

성공과 실패 모두 실제 HTTP 상태 코드와 `status` 값이 일치한다.

```json
{"status": 200, "msg": "OK", "data": {}}
```

- 목록의 data: `{rooms, total, limit, offset}`.
- 생성·입장·상세·방 설정·강퇴·양도의 data: `{room, me, members, markers}`.
- `room`: id, name, map_id, is_locked, max_members, member_count, create_time, update_time.
- `members`에는 마커 작성자를 표시할 수 있도록 퇴장·강퇴 이력도 포함한다.
  현재 참여자 목록은 `status == "joined"`로 필터링한다.
- 계정 이메일과 비밀번호 해시는 응답에서 제외한다. 인증 주체는 서버가 확인한 이메일이며,
  요청 본문의 이메일/작성자 ID/권한 값은 받지 않는다.

**`member_count`는 입장 상태(joined)의 인원이며 실시간 온라인 접속자 수가 아니다.**
실시간 온라인 인원은 WebSocket snapshot의 `presence.online_count`를 사용한다.
새로고침 시 WebSocket에 다시 인증하면 상태를 복원하며, 퇴장 버튼은 leave API를 호출한다.
정상 연결 종료 후 90초 동안 재접속하지 않으면 자동 퇴장한다. 비정상 종료는
45초 연결 만료 감지 및 정리 주기에 따라 더 늦게 정리될 수 있다.
REST 입장 후 WebSocket에 연결하지 않는 경우에도 유예 후 자동 퇴장한다.

방장이 퇴장하면 입장 시각이 가장 빠른 남은 참여자에게 자동 양도한다.
마지막 참여자의 명시적 퇴장 또는 방장의 DELETE 요청은 즉시 방을 종료한다.
종료는 soft close이며 기록을 물리 삭제하지 않는다. 종료 방은 목록에서 제외하며
상세·입장·수정 요청에 410을 반환한다. 강퇴 계정은 같은 방에 재입장할 수 없다.

## 주요 오류

| HTTP | msg 예시 | 의미 |
| --- | --- | --- |
| 401 | LOGIN_REQUIRED / INVALID_TOKEN | 로그인 필요 / 토큰 무효 |
| 403 | REGISTERED_USER_REQUIRED | 사이트 계정 등록 필요 |
| 403 | INVALID_ROOM_PASSWORD / ROOM_LOCKED | 잘못된 비밀번호 / 신규 입장 잠김 |
| 403 | PARTY_MEMBER_KICKED / PARTY_MEMBERSHIP_REQUIRED | 강퇴됨 / 입장 자격 없음 |
| 403 | PARTY_OWNER_REQUIRED / MARKER_OWNER_REQUIRED | 방장 또는 마커 편집 권한 필요 |
| 404 | ROOM_NOT_FOUND / MEMBER_NOT_FOUND / MARKER_NOT_FOUND | 대상 없음 또는 다른 방의 대상 |
| 409 | ROOM_FULL / CAPACITY_BELOW_MEMBER_COUNT | 정원 초과 / 현재 인원보다 작은 정원 |
| 409 | MEMBER_COLOR_IN_USE / MARKER_VERSION_CONFLICT | 색상 중복 / 오래된 마커 버전 |
| 409 | OWNER_MUST_LEAVE_OR_TRANSFER / ROOM_MARKER_LIMIT | 자신을 강퇴할 수 없음 / 마커 수 제한 |
| 409 | PARTY_STATE_CONFLICT | DB 무결성 충돌 |
| 410 | ROOM_CLOSED | 종료된 방 |
| 422 | INVALID_REQUEST / LIVE_MAP_NOT_AVAILABLE / FLOOR_NOT_IN_ROOM_MAP | 입력·맵·층 오류 |
| 429 | TOO_MANY_ATTEMPTS | Retry-After 헤더 시간 후 재시도 |
| 503 | AUTH_UNAVAILABLE / PARTY_RATE_LIMIT_UNAVAILABLE / PARTY_DATABASE_UNAVAILABLE | 의존 서비스 장애 |

계정별 생성은 분당 5회, 입장 요청은 전체 방 합계 분당 30회 및 방별 분당 5회,
비밀번호 변경 요청은 분당 5회로 제한한다. 성공/실패 모두 요청 횟수에 포함한다.
제한 값은 `PartyServiceV3`에서 관리하고, Redis의 원자적 카운터와 TTL을 사용한다.

## 검증과 운영

테스트 실행 및 환경 조건은 [WebSocket 문서](live_map_party_v3_websocket.md)의 검증 항목을 참고한다.
권한, 비밀번호, 정원, 강퇴, 방장 양도, 층 관계, 버전 충돌, DB 실패 롤백과
실시간 메시지 전달·재접속·자동 퇴장을 검증한다. 운영 DB에는 테스트로 접속하지 않는다.

기존처럼 FastAPI를 실행하면 파티 라우터의 lifespan이 자동 정리 작업을 시작한다.
15초마다 최대 100개의 열린 방을 순회하며, 동시 정리 작업은 방 행 잠금으로 조정한다.
방이 많으면 한 바퀴 순회하는 데 더 오래 걸린다. `PARTY_CLEANUP_ENABLED=false`로
정리 작업을 끌 수 있으나 이 경우 접속이 끊긴 참여자는 자동 퇴장하지 않는다.
Redis 오류 중에는 정리를 보류하고, Redis 데이터가 유실되면 새 유예 시간을 부여한다.
닫힌 방의 DB 기록은 보관하며 물리 삭제 스케줄러는 포함하지 않는다.
