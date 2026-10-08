# 모집 채팅 현재 접속자 목록 — 프론트 연동 안내

작성일: 2026-10-09. URL은 `API_PREFIX=/api` 기준이며 실제 환경의 API base URL을 사용한다.

## 화면 요구사항

‘내 위치 찾기’ 페이지의 파티 모집 채팅 옆 또는 상단에 **현재 접속자 N명**과 닉네임 목록을 표시한다. 모든 사용자에게 표시하며 관리자 여부로 숨기지 않는다. 비로그인 사용자도 목록을 볼 수 있다.

목록은 **채팅 WebSocket에 연결된 로그인 사용자**다. 메시지를 쓰지 않아도 포함한다. ‘내 위치 찾기’ 진입 시 기존 채팅 WebSocket을 자동 연결하면 해당 페이지를 이용하는 로그인 사용자가 표시된다. 프론트의 자동 연결 여부는 확인이 필요하다.

- 전체 모집 채팅 기준이며 지도·층·파티별 목록이 아니다.
- 본인도 포함한다. 자기 표시가 필요하면 `snapshot.data.user.id`와 비교한다.
- 같은 계정이 여러 탭으로 접속해도 한 명이다.
- 닉네임이 같은 계정은 서로 다른 사용자다. React key 및 식별에는 `id`를 사용한다.
- 비로그인 사용자는 목록과 인원수에 포함되지 않는다. ‘페이지 전체 방문자 수’라고 표시하지 않는다.
- 차단한 사용자도 접속자 목록에는 표시된다. 차단은 메시지 필터에만 적용된다.
- 서버가 닉네임, 공개 ID 순으로 정렬한다. 이메일·사진은 제공하지 않는다.

## 기존 채팅 WebSocket에 연결

주소: `wss://<API_HOST>/api/live-map/v3/chat/ws` (로컬 HTTP 환경은 `ws://`). 기존 채팅 연결을 재사용하며 목록용 WebSocket을 추가로 열지 않는다.

연결 후 10초 안에 최초 패킷을 보낸다. 토큰을 URL query에 넣지 않는다.

```json
{"type":"auth","token":"<Google access token>"}
```

비로그인은 다음 패킷을 보낸다.

```json
{"type":"guest"}
```

로그인/로그아웃 시 기존 연결을 닫고 해당 모드로 재연결한다. 잘못된 토큰에 대한 인증 실패를 자동으로 guest 모드로 바꾸지 않는다. 페이지를 나가면 연결과 heartbeat 타이머를 정리한다. 채팅 탭을 접거나 지도·층을 바꿀 때 연결을 유지하면 계속 접속자로 표시된다.

## 초기 목록과 실시간 갱신

기존 `snapshot.data`에 `online_users`가 추가되었다. 아래 snapshot 예시는 접속자 관련 필드만 발췌했으며 기존 메시지·파티 필드도 계속 전달된다.

```json
{
  "type": "snapshot",
  "event_id": "<UUID>",
  "server_time": "2026-10-09T03:00:00+00:00",
  "data": {
    "user": {"id": "11111111-1111-4111-8111-111111111111", "nickname": "타르코프유저"},
    "online_users": [
      {"id": "11111111-1111-4111-8111-111111111111", "nickname": "타르코프유저"}
    ],
    "heartbeat_interval_seconds": 30
  }
}
```

접속자 목록이 바뀌면 다음 이벤트를 받는다. `data`는 **전체 목록**이므로 기존 배열을 교체한다. 추가/삭제분으로 처리하거나 기존 배열에 이어 붙이지 않는다.

```json
{
  "type": "online_users_updated",
  "event_id": "<UUID>",
  "server_time": "2026-10-09T03:00:02+00:00",
  "data": [
    {"id": "11111111-1111-4111-8111-111111111111", "nickname": "타르코프유저"},
    {"id": "22222222-2222-4222-8222-222222222222", "nickname": "파티원"}
  ]
}
```

TypeScript 적용 예시 (기존 메시지 핸들러에 추가):

```ts
type ChatOnlineUserV3 = { id: string; nickname: string };

type OnlineUsersEventV3 =
  | { type: "snapshot"; data: { online_users?: ChatOnlineUserV3[] } }
  | { type: "online_users_updated"; data: ChatOnlineUserV3[] };

function applyOnlineUsersV3(event: OnlineUsersEventV3) {
  const users = event.type === "snapshot" ? event.data.online_users : event.data;
  if (Array.isArray(users)) {
    setOnlineUsers(users); // React state: ChatOnlineUserV3[]
    setPresenceStatus("ready");
  }
}
```

`setOnlineUsers`와 `setPresenceStatus`는 화면 상태 setter 예시다. 기존 snapshot 처리와 함께 실행하며 인원수는 `onlineUsers.length`로 표시한다. 닉네임은 일반 텍스트로 렌더링한다.

## 연결 상태와 빈 목록

- 첫 snapshot 전: ‘접속자 확인 중’. 초기 빈 배열을 곧바로 ‘0명’으로 표시하지 않는다.
- 정상 수신된 `[]`: ‘현재 접속 중인 로그인 사용자가 없습니다.’
- 연결이 끊기거나 조회 실패: ‘접속자 정보 재연결 중’ 또는 ‘접속자 정보를 불러오지 못했습니다.’ 마지막 목록을 유지한다면 최신 정보가 아님을 표시한다.
- `online_users` 필드가 없는 구버전 snapshot: 미지원/확인 중 상태로 처리한다. 실제 빈 목록으로 해석하지 않는다.
- 로그인 사용자 연결이 완료되면 본인이 포함되므로 통상 최소 1명이다. 게스트에게는 0명이 표시될 수 있다.

서버는 약 2초마다 목록 변경을 확인한다. 정상 종료 시 다른 탭이 없으면 목록에서 제거한다. 서버 중단 등 비정상 종료는 마지막 연결 갱신 후 최대 90초 만료와 다음 확인 주기까지 지연될 수 있다.

기존처럼 30초마다 `{"type":"heartbeat"}`를 전송한다. 응답 snapshot의 `online_users`도 다시 적용한다. 75초 동안 정상 명령이 없으면 연결이 종료된다. 15분마다 `SESSION_REFRESH_REQUIRED`/종료 코드 1012를 받으면 로그인 사용자는 토큰을 갱신해 auth로, 비로그인은 guest로 재연결한다. 재연결은 지수 backoff와 jitter를 사용하고 새 snapshot으로 목록을 복구한다. 재접속 중 인원수는 잠시 변할 수 있다.

## REST 조회가 필요한 경우

`GET /api/live-map/v3/chat/online-users`

비로그인 조회는 Authorization 헤더를 생략한다. 로그인 조회는 기존 Bearer 토큰을 사용한다. 실시간 화면은 WS를 기준으로 처리하면 되므로 별도 REST polling은 필요 없다.

```json
{
  "status": 200,
  "msg": "OK",
  "data": [
    {"id": "11111111-1111-4111-8111-111111111111", "nickname": "타르코프유저"}
  ]
}
```

응답은 `Cache-Control: private, no-store`다. Redis 장애 시 503 `CHAT_PRESENCE_UNAVAILABLE`을 반환한다. 실패를 빈 목록/0명으로 바꾸지 않는다. REST만 호출한 사용자는 접속자 목록에 등록되지 않는다.

## 배포 및 확인

현재 백엔드에는 접속 이력 저장도 포함되어 있으므로 배포 전에 V3 DB에 `sql/migrations/20261009_chat_connections_v3.sql`을 적용해야 한다. 운영 적용과 프론트 연동은 별도로 진행한다. 이 화면에서는 공개 `/chat/online-users`와 채팅 WS를 사용한다. 관리자 전용 `/chat/admin/connections`는 이 화면 연동 대상이 아니다.

1. 로그인 사용자 A가 페이지에 진입하면 본인 닉네임이 표시되는지 확인한다.
2. 사용자 B가 진입하면 A/B 양쪽 목록과 인원수가 갱신되는지 확인한다.
3. A의 다른 탭을 열어도 한 명으로 유지되고 한 탭만 닫아도 남아 있는지 확인한다.
4. B의 마지막 연결 종료 후 목록에서 제거되는지 확인한다.
5. 비로그인으로 목록을 볼 수 있고 본인은 인원수에 포함되지 않는지 확인한다.
6. 지도·층 변경, heartbeat, 재인증 후에도 목록이 정상 복구되는지 확인한다.
7. 서버 연결 실패와 실제 0명 상태를 다르게 표시하는지 확인한다.

전체 채팅 계약: [live_map_chat_v3_api.ko.md](live_map_chat_v3_api.ko.md).
