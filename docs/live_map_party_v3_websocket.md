# Live Map 파티 V3 — 프론트 연동 계약

[REST API 문서](live_map_party_v3_api.md)와 이 문서를 함께 읽고 구현한다.
방 관리·지속 마커 저장은 REST, 즉시 전달과 접속 관리는 WebSocket을 사용한다.
DB 변경 없이 기존 파티 테이블 3개와 Redis를 사용한다.

## 화면 구현 순서

1. 공개 방 목록: 이름 검색, 맵 필터, 입장 인원/정원, 입장 잠금 표시.
2. 로그인한 사용자만 생성·입장 버튼 사용. 방 생성 폼 또는 비밀번호 입력 후 REST 호출.
3. 성공 응답의 room.id로 아래 WebSocket에 연결하고 첫 snapshot을 적용한다.
4. 참여자 닉네임·색상, 온라인 상태, 지도 마커·핑·수동 위치를 표시한다.
5. 방장 메뉴에 설정·강퇴·방장 양도·방 종료를, 모든 참여자에게 퇴장 버튼을 제공한다.
6. 연결 중에는 변경 REST 응답을 성공 확인 용도로 사용하고, 지도 상태는 WebSocket snapshot으로
   갱신한다. REST 응답이 늦게 도착해서 최신 WebSocket 상태를 덮어쓰지 않게 한다.
   필요하면 변경 성공 후 `sync`를 전송해 최신 상태를 요청한다.

확대/축소, 지도 이동, 선택한 층은 각자의 화면 상태다. 다른 층의 핑을 받은 경우
해당 층에 알림 배지를 표시할 수 있지만 상대의 화면 이동을 강제하지 않는다.
마커의 위치에는 기존 live map `floor_id`, `x`, `z`를 사용한다.

## 연결 및 인증

경로: `WS {API_PREFIX}/live-map/v3/party/rooms/{room_id}/ws`.
예: `wss://backend.example/api/live-map/v3/party/rooms/방UUID/ws`.
기존 알림용 `/ws`와는 별도 연결이다. 운영에서는 HTTPS와 WSS를 사용한다.

연결 후 **10초 안에** 첫 JSON 메시지로 인증한다:

```json
{"type":"auth","token":"Google access token"}
```

- 토큰은 URL 쿼리·방 이름에 넣지 않는다. 서버 응답에도 토큰이 포함되지 않는다.
- WebSocket 연결은 방 입장을 대신하지 않는다. 먼저 REST 생성 또는 입장에 성공해야 한다.
- 새로고침/재접속 시 joined 상태라면 비밀번호 입장 API를 반복하지 않고 WebSocket만 다시 연다.
- 접속은 계정·방당 최대 5개이며, 여러 탭을 열어도 온라인 인원에는 한 명으로 집계한다.
- 프레임은 UTF-8 텍스트 JSON, 최대 8,192바이트다. 서버는 바이너리 메시지를 받지 않는다.

인증 성공 직후 현재 상태를 담은 `snapshot`이 온다. 이후 **15초마다 heartbeat**를 전송한다:

```json
{"type":"heartbeat"}
```

heartbeat 응답도 전체 `snapshot`이다. 별도 `pong` 이벤트는 없다.
즉시 재동기화가 필요하면 `{"type":"sync"}`를 보낸다.
45초 동안 유효한 클라이언트 메시지가 없으면 연결을 닫는다.
연결은 최대 15분 유지하며 이후 `SESSION_REFRESH_REQUIRED`와 1012 종료 코드로
새 인증 연결을 요청한다. 재연결 시 로그인 세션에서 유효한 토큰을 가져온다.

## 클라이언트 → 서버

| type | 필드 | 동작 |
| --- | --- | --- |
| auth | token | 첫 메시지에서만 로그인 인증 |
| heartbeat | 추가 필드 없음 | 연결 유지와 전체 상태 복원 |
| sync | 추가 필드 없음 | 전체 상태 다시 받기 |
| ping | floor_id, x, z, marker_type?, label?, request_id? | 5초간 표시할 순간 핑 |
| position | floor_id, x, z, yaw?, request_id? | 참여자의 최신 위치, 60초 유효 |

순간 핑:

```json
{
  "type":"ping",
  "floor_id":"live_map_floors.id",
  "x":125.5,
  "z":-48.25,
  "marker_type":"danger",
  "label":"적 발견",
  "request_id":"local-ping-1"
}
```

수동 위치:

```json
{"type":"position","floor_id":"live_map_floors.id","x":120,"z":-40,"yaw":90,"request_id":"local-position-1"}
```

- `request_id`는 선택, 최대 64자다. 서버 이벤트에 그대로 포함되어 자신의 요청과 연결할 수 있다.
- `marker_type`은 REST와 동일하며 기본 normal, label은 선택이며 최대 100자다.
- `member_id`, nickname, color, 만료 시각, membership_epoch는 서버가 결정한다.
  클라이언트가 보내면 유효성 오류다. 방에 속하지 않는 층과 유한하지 않은 좌표도 거절한다.
- 위치는 실제 게임 좌표를 자동 추적하는 기능이 아니다. 새 위치 메시지를 보내지 않으면
  60초 후 사라지고, heartbeat가 위치 유효 시간을 연장하지 않는다.
- 지속 마커의 생성·수정·삭제는 REST API를 사용한다. WebSocket에 해당 명령을 보내지 않는다.
- 계정·방별 일반 메시지 합계 분당 120회, 그중 ping 분당 30회로 제한한다.
  heartbeat와 sync도 합계에 포함하며 여러 탭은 한 계정의 제한을 공유한다.

## 서버 → 클라이언트

정상 이벤트의 공통 구조:

```json
{
  "type":"snapshot",
  "event_id":"서버가 생성한 UUID",
  "room_id":"방 UUID",
  "server_time":"2026-09-21T10:00:00+00:00",
  "data":{}
}
```

| type | data | 프론트 처리 |
| --- | --- | --- |
| snapshot | room, me, members, markers, presence, positions, heartbeat_interval_seconds, reconnect_grace_seconds, reason | 저장 상태 전체 교체 |
| ping | member_id, membership_epoch, nickname, color, floor_id, x, z, marker_type, expires_at, label?, request_id? | 만료 시각까지 순간 핑 표시 |
| position | member_id, membership_epoch, nickname, color, floor_id, x, z, yaw?, expires_at, request_id? | 참여자별 최신 위치 갱신 |
| error | 공통 정상 이벤트 구조와 다름. 아래 오류 형식 참고 | 오류 표시/재접속 판단 |

snapshot.data 예시(배열의 상세 객체는 REST 스키마와 동일):

```json
{
  "room":{"id":"방 UUID","name":"우리 파티","map_id":"맵 ID","is_locked":false,"max_members":5,"member_count":2,"create_time":"2026-09-21T10:00:00+00:00","update_time":"2026-09-21T10:00:00+00:00"},
  "me":{"id":"내 참여자 UUID","nickname":"플레이어1","color":"#EF4444","role":"owner","status":"joined","joined_at":"2026-09-21T10:00:00+00:00"},
  "members":[],
  "markers":[],
  "presence":{"online_member_ids":["내 참여자 UUID"],"online_count":1},
  "positions":[],
  "heartbeat_interval_seconds":15,
  "reconnect_grace_seconds":90,
  "reason":"connected"
}
```

- 예시의 members/markers는 생략을 위해 빈 배열로 표시했다. 실제 members에는 자신도 포함된다.
- `reason`: `connected`, `changed`, `heartbeat`, `sync` 중 하나.
- `room.member_count`는 입장 자격을 가진 인원, `presence.online_count`는 현재 접속 인원이다.
- members에는 기존 마커의 작성자를 표시할 수 있도록 퇴장·강퇴 참여자도 포함한다.
  참여자 UI에는 status가 joined인 사람만 표시하고 online_member_ids로 접속 배지를 붙인다.
- positions는 **position 이벤트 전체 객체의 배열**이다. 각 객체의 data.member_id로 위치를 찾는다.
- `expires_at`은 밀리초가 아닌 Unix 초 실수다. server_time으로 서버/브라우저 시각 차이를
  보정한 뒤 만료된 핑·위치를 제거한다. snapshot에는 만료된 위치와 과거 핑이 포함되지 않는다.
- `membership_epoch`는 재입장 세대를 구분하는 서버 문자열이다. 이전 입장 세대의 위치를
  새 참여 상태에 재사용하지 않는다. snapshot의 positions를 기준으로 상태를 다시 맞춘다.
- 자신의 핑/위치도 같은 방 방송으로 돌아온다. event_id로 중복을 제거하고,
  위치는 member_id별 server_time을 비교해 이전 이벤트가 최신 위치를 덮어쓰지 않게 한다.
- snapshot은 지속 상태를 교체한다. 순간 핑 배열은 따로 관리하고 expires_at으로 지운다.
  REST 후 바뀐 room/me/members/markers가 snapshot으로 오므로 별도 marker.created 이벤트는 없다.

## 퇴장·재접속과 자동 정리

- 퇴장 버튼: 자동 재접속을 중단 → REST leave 요청 → WebSocket 종료 → 목록 화면.
- 방 종료/강퇴/퇴장 시 서버는 권한을 재확인하고 해당 연결을 닫는다.
  같은 계정이 다시 입장해도 이전 연결은 새 입장 권한을 자동으로 얻지 않는다.
- 새로고침·일시적인 연결 종료에는 leave를 호출하지 않는다. 유예 안에 재접속하면
  같은 참여자 ID, 색상, 방장 권한을 유지한다.
- 정상 연결 종료 후 90초 동안 복구되지 않으면 자동 퇴장한다. 비정상 종료는
  연결 만료(최대 45초) 감지, 유예와 정리 주기에 따라 더 늦게 처리될 수 있다.
- 방 생성/입장 후 WebSocket을 열지 않아도 자동 퇴장 대상이다.
- 자동 퇴장 대상이 방장이면 남은 참여자에게 양도하고, 마지막 사람이면 방을 종료한다.
- Redis 오류 동안에는 자동 퇴장을 보류한다. Redis가 초기화되면 새 유예 시간을 부여한다.
- 종료 방의 기록은 DB에 남기며, 이미 종료된 방은 재접속할 수 없다.

오류 메시지는 다음 형식이다. 요청 내용/토큰을 반사하지 않는다:

```json
{"type":"error","status":429,"msg":"TOO_MANY_ATTEMPTS","retry_after":37}
```

status 422의 INVALID_MESSAGE/FLOOR_NOT_IN_ROOM_MAP은 입력을 수정해서 계속 사용할 수 있다.
형식 오류가 누적 3회면 연결을 종료한다. 429는 retry_after 초 뒤 다시 전송한다.
연결 수 제한은 다른 탭의 파티 연결을 닫은 뒤 재시도한다.

| 종료 코드 | 의미 / 프론트 처리 |
| --- | --- |
| 4401 | 로그인 인증 실패. 로그인 갱신 후 재시도 |
| 4403 | 입장 권한 없음, 퇴장 또는 강퇴, 재입장 세대 변경. 자동 재시도 중단, 방 목록/입장 화면 |
| 4404 | 방 없음. 목록으로 이동 |
| 4408 | 인증 또는 heartbeat 시간 초과. 유효한 토큰과 정상 heartbeat로 다시 연결 |
| 4410 | 종료된 방. 자동 재시도 중단, 목록으로 이동 |
| 4429 | 연결 생성/연결 수 제한. 오류 안내 후 대기 |
| 1008 / 1009 | 메시지 형식/크기 위반. 자동 재시도 중단, 클라이언트 처리 점검 |
| 1012 | 15분 세션 갱신. 유효한 토큰을 받아 재접속 |
| 1013 / 비정상 네트워크 종료 | 서비스/통신 장애. 지수 백오프와 임의 지연으로 재접속 |

재접속 지연은 예를 들어 1→2→4→8→최대 30초로 늘리고 임의 지연을 더한다.
네트워크 복구 후 첫 snapshot을 받은 뒤 연결 완료로 표시한다.
유예가 지나 joined 상태가 해제됐다면 비밀번호 입장부터 다시 진행한다.

## 최소 JavaScript 연결 예시

```js
// backendHttpBase: 예) https://backend.example/api
// 이미 REST로 방에 입장했고 유효한 accessToken을 확보한 뒤 실행한다.
const url = new URL(`${backendHttpBase}/live-map/v3/party/rooms/${roomId}/ws`);
url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(url);
let heartbeatTimer;

ws.onopen = () => ws.send(JSON.stringify({type: 'auth', token: accessToken}));
ws.onmessage = ({data}) => {
  const event = JSON.parse(data);
  if (event.type === 'snapshot') {
    applyPartySnapshot(event.data); // room/me/members/markers/presence/positions 교체
    if (!heartbeatTimer) {
      heartbeatTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({type: 'heartbeat'}));
        }
      }, event.data.heartbeat_interval_seconds * 1000);
    }
  } else if (event.type === 'ping' || event.type === 'position') {
    applyTemporaryPoint(event); // event_id 중복 제거 + expires_at 만료 처리
  } else if (event.type === 'error') {
    showPartyError(event.msg, event.retry_after);
  }
};
ws.onclose = ({code}) => {
  clearInterval(heartbeatTimer);
  handlePartyClose(code); // 위 종료 코드 표에 따라 재접속 또는 목록 이동
};
```

백그라운드 탭에서 타이머가 제한될 수 있으므로 focus/online 복귀 시 연결 상태를 확인한다.
닉네임과 label은 일반 텍스트로 렌더링한다. HTML로 직접 삽입하지 않는다.

## 운영 및 검증

- 기존 FastAPI 앱에 등록된 파티 라우터가 REST, WebSocket, 자동 정리 lifespan을 함께 제공한다.
- 서버 워커는 같은 V3 DB와 Redis를 사용해야 한다. Redis Pub/Sub로 워커 간 전달한다.
- reverse proxy는 해당 경로의 WebSocket Upgrade를 허용하고 heartbeat 간격보다 긴 연결 제한을 둔다.
- 신규 DB 테이블/컬럼이나 런타임 패키지 추가는 없다. `PARTY_CLEANUP_ENABLED`는 기본 true다.
- Pub/Sub는 이벤트 재생 저장소가 아니다. 일시적인 알림 유실은 15초 heartbeat snapshot이나
  재접속 snapshot으로 복구한다. 지난 순간 핑은 재생하지 않는다.

격리 테스트 실행(개발용 fakeredis[lua] 필요):

```sh
uv pip install --python .venv/bin/python 'fakeredis[lua]==2.38.0'
.venv/bin/python -m unittest tests.test_live_map_party_v3 tests.test_live_map_party_realtime_v3 -v
```

SQLite + 가상 Redis 테스트는 REST 권한/롤백, 두 소켓 간 핑과 마커 변경 전달,
강퇴/종료 연결 차단, 위치 복원, 누락 알림 복구, 여러 탭 인원 집계, 자동 방장 양도·종료,
Redis 장애 시 정리 보류, 이전 입장 연결 무효화, 메시지 제한을 검증한다.

실제 로컬 PostgreSQL/Redis 통합 테스트(개발용 서버 패키지 선택 설치):

```sh
uv pip install --python .venv/bin/python 'pgserver==0.1.4' 'redislite==6.2.912183'
.venv/bin/python -m unittest tests.test_live_map_party_postgres_v3.PartyPostgresTestV3 -v
```

테스트가 임시 디렉터리와 Unix 소켓에 PostgreSQL/Redis를 시작하고 종료한다.
운영 DB나 Redis 주소를 사용하지 않는다. 실제 동시 입장 정원 제한, 동시 수정 버전 충돌,
FK/체크 제약과 방 삭제 cascade, 소켓 전달·강퇴·방장 자동 양도를 검증한다.
`platform_db.sql`의 관련 DDL을 그대로 읽되, 번들 PostgreSQL에 pg_trgm이 없어
이 테스트에서만 방 이름 검색용 GIN 인덱스를 제외한다. 운영 스키마는 변경하지 않는다.

### 위치 방향 (`yaw`)

`position.yaw`는 선택 필드이며 기존 위치 쿼터니언에서 계산한 원본 방향(도 단위, 0 이상 360 미만)을 전달한다. 지도 회전이나 맵별 표시 보정은 클라이언트가 렌더링할 때 적용한다. 생략/null이면 방향 미상으로 취급하며 이전 방향을 유지하지 않는다. NaN, 무한대, 범위 밖 값은 거부한다.

서버는 yaw를 같은 방의 position 방송과 Redis 위치 캐시에 포함하고, 재접속 snapshot.positions에서도 그대로 반환한다. 방향 없는 구형 클라이언트도 허용한다. 프론트가 yaw를 보내기 전에 이 스키마가 반영된 백엔드를 먼저 배포해야 한다.

### 기존 위치 전송과 파티 공유

현재 프론트 연동 흐름은 `send-location → 개인 WebSocket의 wpf_location → 송신자의 웹페이지 → 파티 WebSocket의 position → 같은 방의 참여자`이다. 웹페이지가 위치 문자열을 파싱하고 층을 결정하여 좌표와 방향을 전달한다. 기존 `send-location` API가 직접 파티 채널에 방송하는 구조는 아니다.

- 송신자의 웹페이지가 파티 WebSocket에 연결된 상태에서 새 위치를 받아야 공유된다. 연결 전에 받은 위치는 자동 재전송하지 않는다.
- 현재 프론트는 관리자 계정만 파티 연결을 허용하므로 양방향 검증에는 관리자 계정 두 개가 필요하다.
- 프론트는 선택한 층과 같은 `floor_id`의 위치만 표시한다. 다른 층의 위치는 해당 층으로 전환해서 확인한다.
- 위치는 60초 후 만료된다. heartbeat만으로 위치 유효 시간이 연장되지는 않는다.
- `yaw`를 허용하지 않는 구버전 백엔드에 새 프론트를 연결하면 `INVALID_MESSAGE`로 위치 메시지 전체가 거절된다. 백엔드 스키마를 먼저 배포한 뒤 같은 방의 두 계정에서 각각 새 위치를 전송하여 확인한다.
