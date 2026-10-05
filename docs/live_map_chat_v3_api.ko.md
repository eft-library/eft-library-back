# 라이브 맵 모집·파티 채팅 V3 연동 계약

구현 기준: 2026-10-03. 아래 URL은 `API_PREFIX=/api`를 전제로 한다. 기존 `/ws`, 위치 수신, `send_location`, 파티 REST/WS, 위치·지도·마커 이벤트는 유지한다. 채팅 연결은 지도·층 전환 시 끊지 않는다.

## 확정 정책

- **비로그인 사용자는 모집(lobby) 채팅의 과거 메시지 조회와 실시간 읽기가 가능하다.** 파티 채팅 조회, 메시지 작성, 초대·차단·신고·관리 기능은 로그인 및 `user_info` 등록이 필요하다. 로그인 REST는 `Authorization: Bearer <Google access token>`을 사용한다. 서버가 계정·권한을 조회한다.
- **초대 생성은 현재 방장만 가능하다.** 일반 멤버는 `PARTY_OWNER_REQUIRED`(403)를 받는다. 방장 양도 전에 생성된 초대는 만료·취소 전까지 유효하다.
- 채팅 제재는 전송에만 적용한다. 일시·영구 제재 중에도 읽기는 가능하다.
- 차단은 단방향: 내가 차단한 상대의 메시지가 내 조회·실시간 수신에서 제외된다. 상대방의 조회나 파티 권한을 변경하지 않는다.
- 사용자 표시 필드는 **닉네임만**이다. `user: {id: UUID, nickname: string}`의 `id`는 초대·차단 식별용 공개 UUID다. 이메일과 프로필 사진 필드는 반환하지 않는다. 닉네임은 계정 DB에서 조회하며 클라이언트 값을 사용하지 않는다.
- 공개 UUID는 신규 `live_map_chat_users`에 계정별로 생성한다. 기존 계정과 파티 멤버 ID는 변경하지 않는다. 채팅에 한 번도 접근하지 않은 계정의 공개 UUID는 아직 없으며 임의 이메일 검색 API는 제공하지 않는다.
- 메시지는 순수 텍스트로 저장·전달한다. HTML로 해석하지 않는다. 프론트는 React 텍스트 노드/textContent로 표시하고 `innerHTML`을 사용하지 않는다.
- 기존 파티 API의 여러 방 참여 동작은 유지한다. snapshot의 기본 파티는 현재 참여 중인 열린 방 중 가장 최근 입장한 방이다. 명시적 `room_id`를 사용하는 조회·전송은 그 방의 현재 참여 권한을 검사한다. 새로운 초대 수락은 이미 어느 방에든 참여 중이면 거절하며, 신규 초대끼리의 동시 수락도 직렬화한다. 기존 비밀번호 입장 API의 다중 방 참여 정책 자체는 바꾸지 않는다.

## 배포

별도 기능 플래그나 활성화 명령 없이 백엔드 배포 후 신규 REST·WebSocket을 바로 사용할 수 있다. DB 마이그레이션을 백엔드 배포보다 먼저 적용한다.

1. V3 DB에 `sql/migrations/20261003_live_map_chat_v3.sql`만 적용한다. 운영 DB 전체에 `platform_db.sql`을 재실행하지 않는다.
2. 이 마이그레이션은 신규 테이블·인덱스만 추가하고 기존 계정·파티·마커 행을 수정하지 않는다. 트랜잭션, 3초 lock timeout, 30초 statement timeout을 사용한다. timeout 발생 시 전체 rollback 후 트래픽이 낮을 때 재시도한다. 동일 파일 재실행 가능. 이전 `_v3` 접미사 테이블이 이미 있으면 데이터를 유지하며 접미사 없는 이름으로 변경한다. 두 이름의 테이블이 동시에 있으면 자동 병합하지 않고 전체 rollback한다. 기존 채팅 백엔드가 실행 중이면 테이블 이름 변경과 새 백엔드 교체를 같은 점검 시간에 진행한다.
3. 백엔드를 배포하고 기존 로그인·위치 표시·파티 입장·방향 공유·지도 전환·마커 공유와 신규 채팅·초대 API를 점검한다. 기존 `REDIS_URL` 또는 `REDIS_HOST`, Google 인증 설정, V3 DB 설정을 사용한다.
4. 테스트 계정으로 신규 API/WS를 검증한 뒤 실제 운영 응답을 기준으로 신규 프론트를 개발·배포한다. 채팅 WS 프록시의 idle timeout은 75초보다 길게 설정한다.
5. 백엔드 롤백이 필요하면 이전 버전을 배포한다. 추가한 테이블은 유지할 수 있으며 기존 파티 상태와 API를 변경할 필요가 없다.

DB/Redis 장애는 신규 요청에서 503으로 처리한다. 저장 후 알림만 실패하면 성공 응답을 유지하고 REST의 `X-Chat-Realtime: unavailable` 또는 WS ack의 `realtime_available: false`로 알린다. 기존 파티/위치 경로는 채팅 테이블·알림에 의존하지 않는다. 채팅의 DB·Redis 사용량은 모니터링해야 한다. 신규 채팅 트랜잭션에만 statement timeout 5초와 lock timeout 2초를 적용한다.

신규 프론트 정식 출시 후에도 캐시된 이전 프론트와 장시간 열린 탭을 고려한다. 레거시 제거는 별도 배포에서 진행하고 대상 API·종료 일정·대체 경로·실제 호출량을 확인한 뒤 결정한다. 이번 변경은 레거시를 제거하지 않는다.

## 이미 생성된 테이블·인덱스의 이름 변경

기존 SQL을 실행했다면 V3 DB에 `sql/migrations/20261004_rename_chat_objects.sql`을 실행한다. 테이블을 이미 변경하고 인덱스만 남아 있는 경우에도 같은 파일을 사용한다. 신규 설치는 `20261003_live_map_chat_v3.sql`만 실행하면 된다.

```sh
psql -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <V3_DB_NAME> -v ON_ERROR_STOP=1 -f sql/migrations/20261004_rename_chat_objects.sql
```

DB 관리 도구에서는 해당 파일 전체를 열어 V3 DB에서 실행해도 된다. 테이블 6개와 그 테이블의 인덱스·자동 생성 제약조건 이름에서 `_v3`를 제거한다. 예를 들어 `live_map_chat_messages_v3` → `live_map_chat_messages`, `idx_chat_messages_v3_history` → `idx_chat_messages_history`, `live_map_chat_messages_v3_pkey` → `live_map_chat_messages_pkey`로 변경한다. 데이터 삭제나 인덱스 재생성은 하지 않으며 FK 관계는 유지된다. 이미 변경된 이름은 건너뛰므로 재실행할 수 있다.

하나의 트랜잭션으로 실행하고 충돌 또는 timeout 발생 시 전체 rollback한다. 접미사가 있는 테이블을 사용하는 백엔드가 실행 중이면 점검 시간에 해당 버전을 중지하고 SQL 적용 후 새 버전을 실행한다. 운영 DB에 `platform_db.sql` 전체를 다시 실행하지 않는다.

## REST 공통

성공: `{status: HTTP 상태 코드, msg: "OK", data: ...}`. 초대 생성의 msg는 `PARTY_INVITATION_CREATED`다. 실패: `{status, msg: 오류 코드, data: null}`. 입력 검증 오류만 `data.errors: [{loc, msg, type}]`를 포함한다. 검증 오류에 토큰·본문·비밀번호 입력값을 되돌려 보내지 않는다.

REST 요청 및 성공 응답 모델은 OpenAPI에 등록된다. WebSocket 명령과 이벤트는 이 문서를 기준으로 한다.

| 메서드 / 경로 (`/api/live-map/v3` 이후) | 요청 | data |
|---|---|---|
| GET `/chat/messages` | `channel=lobby\|party`, 파티는 `room_id`, 선택 `before`, `limit=50`(1~100) | `{messages, next_before}` |
| GET `/chat/blocks` | 없음 | `[{id, nickname}]` |
| POST `/chat/blocks/{user_id}` | 없음 | `{user_id, blocked:true}` |
| DELETE `/chat/blocks/{user_id}` | 없음 | `{user_id, blocked:false}` |
| POST `/chat/messages/{message_id}/report` | `{reason, detail?:string}` | 201 `{id}` |
| POST `/party-invitations` | `{room_id, invitee_user_id}` | 201 초대 객체 |
| GET `/party-invitations` | `status=pending` 기본; accepted/rejected/revoked/expired 가능 | 초대 객체 배열(요청자에게 오거나 요청자가 생성한 초대만) |
| POST `/party-invitations/{id}/accept` | 없음 | 기존 `PartySnapshotV3`: `{room, me, members, markers}` |
| POST `/party-invitations/{id}/reject` | 없음 | 초대 객체 |
| DELETE `/party-invitations/{id}` | 없음 | 초대 객체 |
| GET `/chat/admin/reports` | `limit=50`(1~100), `offset=0`(0~10000) | 신고 배열 |
| DELETE `/chat/admin/messages/{message_id}` | 없음 | `{message_id}` |
| PUT `/chat/admin/restrictions/{user_id}` | `{reason, expires_at: ISO8601\|null}` | `{user_id, restricted:true}` |
| DELETE `/chat/admin/restrictions/{user_id}` | 없음 | `{user_id, restricted:false}` |

관리자 권한은 `user_info.is_admin=true`로 확인한다. 임시 제재의 `expires_at`은 미래의 timezone 포함 시각, 영구 제재는 null이다. 사유는 공백 제외 1~1000자다. 신고 `reason`은 `spam`, `abuse`, `inappropriate`, `personal_info`, `other`; detail은 최대 1000자. 동일 사용자의 같은 메시지 신고는 409다. 관리자는 파티 가입 여부와 무관하게 신고를 조회하고 메시지를 삭제할 수 있다.

신고 객체: `{id, user_id, message_id, reason, detail, create_time, message: 메시지 객체}`. 삭제된 메시지는 본문이 빈 문자열이다.

### 메시지와 페이지 정렬

```json
{
  "id": "message UUID",
  "channel": "lobby",
  "room_id": null,
  "user": {"id": "public user UUID", "nickname": "닉네임"},
  "message": "같이 하실 분 구합니다.",
  "create_time": "2026-10-03T00:00:00+00:00"
}
```

REST 및 snapshot 배열은 **최신순** (`create_time DESC, id DESC`). 프론트가 타임라인에 붙일 때 필요하면 뒤집는다. `next_before`는 해당 페이지 마지막 메시지의 시각·ID·채널·방을 인코딩한 opaque cursor다. 이를 그대로 같은 채널/방의 `before`로 전달하면 더 오래된 메시지를 조회한다. 다른 채널/방의 cursor를 사용하면 422다. cursor는 권한을 부여하지 않으며 매 조회마다 파티 참여 여부를 다시 확인한다.

### 초대 객체와 정책

```json
{
  "id": "invitation UUID",
  "invitation_id": "same invitation UUID",
  "room_id": "room UUID",
  "inviter": {"id": "public user UUID", "nickname": "방장"},
  "invitee_user_id": "public user UUID",
  "status": "pending",
  "status_reason": null,
  "expires_at": "2026-10-03T00:10:00+00:00",
  "party": {
    "id": "room UUID", "name": "야간 퀘스트", "member_count": 2,
    "max_members": 5, "is_locked": false, "closed": false, "can_join": true
  }
}
```

`can_join`은 방의 열림·잠금·정원 조건만 나타낸다. 참가자 개인의 현재 파티 참여·강퇴 여부 등은 수락 시 다시 확인한다. 초대 유효기간은 10분이다. 비밀번호·재사용 입장 토큰·공개 참가 링크를 반환하지 않는다.

같은 방/대상의 pending 초대는 한 개만 유지한다. 자기 자신·이미 파티에 참여 중인 대상·강퇴된 대상에게 생성할 수 없다. 방 종료·잠금·정원도 검사한다. 대상당 유효 pending 초대는 최대 50개, 초대 생성은 방장당 1분에 10회다. 목록은 최대 500개이며 pending을 우선하고 생성 최신순이다.

수락은 지정된 대상만 가능하고, 방·대상 사용자 잠금 후 현재 상태를 다시 검사한다. 비밀번호 확인 없이 기존 파티 멤버를 생성/복원하며 기존 파티 변경 알림을 발행한다. 재사용은 불가능하다. 거절은 대상만, 취소는 생성자 또는 현재 방장만 가능하다.

파티 잠금은 pending을 유지하며 `can_join=false`로 표시한다. 만료는 expired, 종료·정원 도달·해당 방 참가/강퇴는 revoked로 정리한다. `status_reason`은 revoked일 때 `cancelled`, `room_closed`, `room_full`, `already_joined`, `member_kicked` 중 하나이며, pending·accepted·rejected·expired에는 null이다. 기존 데이터 중 이미 revoked였던 행은 null일 수 있으므로 프론트는 일반적인 취소 문구로 처리한다. 기존 파티 경로에 채팅 의존성을 넣지 않기 위해 상태 관찰·정리는 별도 루프로 수행한다. 개인 이벤트는 통상 2초 이내 갱신되며 부하/DB 장애 시 지연될 수 있다. 짧게 정원이 찼다가 다음 관찰 전에 비워지는 경우 pending이 유지될 수 있으나, **수락 시 실제 잠금·정원·강퇴 상태는 항상 검사**한다. 만료·종료·접근 거부는 정리 루프 지연과 무관하게 조회/수락 시 적용된다.

## WebSocket

URL: `/api/live-map/v3/chat/ws`. 기존 파티 WS와 별개다. query string에 토큰을 넣지 않는다. 연결 후 10초 안에 첫 메시지로 로그인 인증 또는 게스트 모드를 선택한다. 로그인 사용자는 기존 auth 형식을 사용한다.

```json
{"type":"auth","token":"Google access token"}
```

비로그인 사용자는 다음 메시지를 보낸다.

```json
{"type":"guest"}
```

게스트는 모집 메시지 및 모집 메시지 삭제 이벤트만 수신한다. snapshot은 `user=null`, `party=[]`, `party_room_id=null`, `party_next_before=null`, `party_invitations=[]`이며 모집 최근 메시지와 cursor는 제공한다. 게스트 계정이나 공개 UUID를 DB에 만들지 않는다. 게스트가 메시지를 전송하면 401 `LOGIN_REQUIRED` 오류만 반환하고 읽기 연결은 유지한다.

REST 비로그인 조회는 `GET /api/live-map/v3/chat/messages?channel=lobby`에 Authorization 헤더를 **생략**한다. 파티 조회는 401이다. 토큰을 보냈지만 잘못되었거나 미등록 계정이면 게스트로 전환하지 않고 기존 인증 오류를 반환한다. WebSocket도 잘못된 auth를 게스트로 전환하지 않는다. 계정 차단 목록은 로그인 조회에만 적용된다. 메시지 조회 응답에는 `Cache-Control: private, no-store`를 설정한다.

프론트는 비로그인 상태에서도 모집 탭을 표시하고 입력창에 로그인 안내를 제공한다. 파티 탭·초대·차단·신고 등 계정 기능은 비활성화한다. 로그인/로그아웃 시 기존 채팅 연결을 닫고 auth/guest 방식으로 다시 연결하여 snapshot으로 UI를 갱신한다. 연결 중 auth/guest 모드 전환은 지원하지 않는다. 이 변경에 추가 DB 마이그레이션은 필요 없다.

로그인 성공 시 snapshot:

```json
{
  "type": "snapshot", "event_id": "UUID", "server_time": "ISO-8601",
  "data": {
    "user": {"id": "public user UUID", "nickname": "나"},
    "lobby": [], "party": [], "party_room_id": null,
    "lobby_next_before": null, "party_next_before": null,
    "party_invitations": [], "heartbeat_interval_seconds": 30
  }
}
```

각 채널은 최근 50개를 포함한다. 파티가 없으면 `party=[]`, `party_room_id=null`. 초대 배열에는 본인에게 온/본인이 생성한 활성 초대를 포함한다. UI의 받은 초대는 `invitee_user_id === data.user.id`로 구분한다.

전송:

```json
{"type":"send_message","channel":"lobby","message":"모집합니다","request_id":"UUID"}
```

```json
{"type":"send_message","channel":"party","room_id":"UUID","message":"3층으로 이동","request_id":"UUID"}
```

닉네임·사용자 ID·권한 필드를 보내지 않는다. 여분 필드는 거절한다. 공백 제거 후 1~300자, 사용자 전체 채널 합산 sliding window 5초당 5개 및 60초당 30개다. 모집 채팅은 같은 사용자가 모집에 보낸 동일 본문만 30초간 반복 전송을 제한한다. 앞뒤 공백을 제거한 뒤 본문 전체가 같은 경우에만 적용한다. 파티 채팅에는 동일 본문 반복 제한이 없고, 모집·파티 사이 동일 본문 전송도 허용한다. 일반 전송 속도 제한과 request_id 중복 방지는 두 채널 모두 유지한다. `request_id`는 사용자별 중복 방지 키로 DB에 저장한다. 중복 요청은 다시 저장/방송하지 않고 기존 ID의 ack만 반환한다. 같은 키를 다른 본문/채널/방으로 재사용하면 409다. 이미 관리자가 본문을 제거한 메시지는 본문 비교 없이 같은 채널/방의 기존 ID만 ack한다. 중복 방지는 메시지 보관 기간 동안 유효하다.

### 전체 명령·이벤트

| 방향 / type | data 또는 요청 필드 |
|---|---|
| 클라이언트 `guest` | 추가 필드 없음, 비로그인 읽기 전용 연결의 최초 메시지 |
| 클라이언트 `auth` | `token` (최초 한 번) |
| 클라이언트 `send_message` | `channel`, `room_id?`, `message`, `request_id` |
| 클라이언트 `heartbeat` | 추가 필드 없음, 30초마다 전송 |
| 서버 `snapshot` | 위 snapshot. 인증/heartbeat/참여 파티 변경 시 발행 |
| 서버 `message_ack` | `{message_id, request_id, duplicate, realtime_available}` |
| 서버 `chat_message` | 메시지 객체 |
| 서버 `party_invitation_created` | 초대 객체. 초대 대상/생성자에게만 전달 |
| 서버 `party_invitation_updated` | 초대 객체. 상태 및 방 정보 변경 시 대상/생성자에게만 전달 |
| 서버 `message_deleted` | `{message_id, channel, room_id}` |
| 서버 `error` | 아래 별도 형식 |

일반 서버 이벤트는 `{type, event_id: UUID, server_time: ISO8601, data}`. 오류는 `{type:"error", status, msg, retry_after: 정수초|null, request_id: UUID|null}`이다. 유효한 `send_message` 처리 중 발생한 오류에는 요청의 `request_id`가 포함되며, 연결·인증·형식 오류에는 null이다. REST 속도 제한은 `Retry-After` 헤더도 제공한다.

전송자도 본인 메시지의 `chat_message`를 받는다. ack와 broadcast 순서는 UI에서 가정하지 않는다. 메시지 `id`로 중복 제거한다. 실시간 권한과 차단은 전달 직전 DB에서 검사한다. 퇴장·강퇴·자동 퇴장·방 종료 이후 새 파티 메시지의 전송/조회/전달을 허용하지 않는다. 파티 상태 표시 snapshot은 별도 관찰 루프에 따라 통상 2초 안에 갱신된다.

프론트는 전송 직후 `sending`, ack 수신 후 `sent`, 같은 `request_id`가 포함된 error 또는 10초 ack timeout 후 `failed`로 표시한다. 재전송은 최초의 `request_id`를 그대로 사용한다. `duplicate=true` ack는 앞선 저장이 성공한 것이므로 sent로 처리한다. `realtime_available=false`도 DB 저장은 완료된 상태이므로 sent로 처리한다. 429는 `retry_after` 이후 사용자가 재시도할 수 있게 하고 자동 무한 재시도는 하지 않는다.

읽지 않은 수는 서버에 저장하거나 여러 기기에서 동기화하지 않는다. 프론트는 탭 메모리 상태로 모집·현재 파티의 unread를 관리하며 새로고침, 로그인 전환, 다른 기기에는 이어지지 않는다. 메시지 목록이 실제로 최하단에 노출됐을 때 해당 채널의 unread를 0으로 만든다. 과거 메시지를 보는 동안 새 메시지가 오면 자동 스크롤하지 않고 `새 메시지 N개` 버튼을 표시한다.

채팅 연결은 기존 파티의 접속 lease를 연장하지 않는다. 위치 공유 및 기존 자동 퇴장 정책을 유지하려면 기존 파티 WebSocket도 계속 사용한다.

### heartbeat·복원·종료

- 30초마다 `{"type":"heartbeat"}`. 응답은 새 snapshot이다. heartbeat는 로그인 사용자별, 게스트 연결별로 1분당 4회 제한. 정상 명령을 75초 동안 받지 못하면 4408 종료.
- 토큰 재검증을 위해 연결 15분 후 `SESSION_REFRESH_REQUIRED` 및 1012 종료. 로그인 사용자는 토큰을 갱신하고 재연결한다. 게스트도 15분 후 같은 종료 코드를 받고 guest 모드로 재연결한다.
- 재연결은 jitter가 있는 지수 backoff(예: 1, 2, 4, 8, 최대 30초). 매번 로그인 사용자는 auth, 비로그인 사용자는 guest를 보내고 snapshot을 처리한다.
- Redis는 메시지 ID 알림과 전송 제한에 사용한다. 본문/이메일/비밀번호/토큰은 알림에 포함하지 않는다. 최근 메시지 원본 조회는 PostgreSQL 인덱스를 사용하며 Redis 본문 캐시는 두지 않는다.
- Redis Pub/Sub는 durable replay가 아니다. 재접속/heartbeat snapshot은 최근 DB 상태를 복구한다. 50개보다 많은 누락은 snapshot의 `*_next_before`와 REST를 사용하여 마지막으로 본 메시지 ID까지 과거 페이지를 가져온다. retention 밖 메시지는 복원되지 않는다.
- snapshot은 최근 구간의 권위 있는 목록이다. 삭제·차단으로 빠진 메시지를 최근 UI 구간에서 제거한다. 오래된 로컬 페이지를 재사용할 때에는 REST로 다시 조회한다. 권한을 잃거나 방이 바뀌면 이전 파티의 UI 메시지를 비운다.
- 4401 인증, 4403 등록/권한, 4408 인증/heartbeat timeout, 4429 연결 속도 제한, 1009 패킷 크기 초과, 1008 잘못된 프로토콜, 1013 DB/Redis/전송 timeout, 1012 세션 재인증.
- 텍스트 JSON만 허용한다. 패킷 최대 8192 UTF-8 바이트. 잘못된 명령 3회 시 종료한다. 느린 수신자는 서버 전송 5초 timeout 적용. 연결 시도는 사용자당 1분 20회, 동시 연결은 5개 제한이다. 게스트는 서버가 인식한 접속 IP별로 동일한 연결 제한을 적용하며 Redis 키에는 IP 해시만 저장한다. 프록시를 쓰면 ASGI 서버의 신뢰 프록시 설정에 따라 실제 클라이언트 IP를 전달해야 한다. Redis 연결 lease는 90초 후 만료하며 정상 종료 시 즉시 해제한다.

## 보관·정리

- 모집 메시지: 생성 후 24시간. 만료된 메시지는 정리 전에도 조회에서 제외.
- 파티 메시지: 방 종료 후 24시간. 닫힌 방 접근은 즉시 거절하고 보관 데이터는 관리자 조회/정리용이다.
- 관리자 삭제: `deleted_at` 기록과 본문 제거. 일반 조회/방송에서 제외.
- 메시지 정리는 60초마다 최대 500개씩. FK cascade로 해당 신고도 삭제한다. 신고 본문 별도 영구 보관은 하지 않는다.
- 초대 상태 정리는 2초마다 최대 100개 방씩, row lock/skip locked 및 순환 cursor로 처리한다. 만료 시각으로부터 7일 지난 초대는 주기적으로 최대 500개씩 삭제한다.
- 정리는 백엔드 lifespan에서 자동 실행하며 시작 시 DB 마이그레이션을 자동 실행하지 않는다. DB 오류 시 다음 주기에 재시도한다.

## 오류 코드

| HTTP | 코드 |
|---|---|
| 401 | `LOGIN_REQUIRED`, `INVALID_TOKEN`, `AUTH_MESSAGE_REQUIRED`, `SESSION_REFRESH_REQUIRED` |
| 403 | `REGISTERED_USER_REQUIRED`, `PARTY_MEMBERSHIP_REQUIRED`, `PARTY_OWNER_REQUIRED`, `CHAT_ADMIN_REQUIRED`, `CHAT_RESTRICTED`, `PARTY_INVITATION_FORBIDDEN`, `PARTY_ROOM_LOCKED`, `PARTY_MEMBER_KICKED` |
| 404 | `CHAT_USER_NOT_FOUND`, `CHAT_MESSAGE_NOT_FOUND`, `PARTY_INVITATION_NOT_FOUND`, `ROOM_NOT_FOUND` |
| 409 | `CHAT_REQUEST_ID_CONFLICT`, `CHAT_ALREADY_REPORTED`, `CHAT_STATE_CONFLICT`, `PARTY_ALREADY_JOINED`, `PARTY_ROOM_FULL`, `PARTY_INVITATION_DUPLICATED`, `PARTY_INVITATION_ALREADY_HANDLED` |
| 410 | `ROOM_CLOSED`, `PARTY_ROOM_CLOSED`, `PARTY_INVITATION_EXPIRED` |
| 422 | `INVALID_REQUEST`, `INVALID_MESSAGE`, `CHAT_INVALID_CHANNEL`, `CHAT_INVALID_CURSOR`, `CHAT_CANNOT_BLOCK_SELF`, `PARTY_CANNOT_INVITE_SELF`, `TEXT_JSON_REQUIRED` |
| 429 | `CHAT_RATE_LIMITED`, `CHAT_REPEATED_MESSAGE`, `CHAT_CONNECTION_LIMIT`, `PARTY_INVITATION_LIMIT` |
| 503 | `AUTH_UNAVAILABLE`, `CHAT_DATABASE_UNAVAILABLE`, `CHAT_RATE_LIMIT_UNAVAILABLE`, `CHAT_UNAVAILABLE`, `PARTY_REALTIME_UNAVAILABLE` |
| 기타 | 408 `AUTH_TIMEOUT`/`HEARTBEAT_TIMEOUT`, 413 `MESSAGE_TOO_LARGE`, 400 `TOO_MANY_INVALID_MESSAGES` |

## 검증

로컬 통합 테스트는 별도 임시 PostgreSQL(`pgserver`)·Redis(`redislite`) 서버와 계정을 생성하며 운영 DB/Redis에 연결하지 않는다.

```sh
.venv/bin/python -m unittest discover -s tests -v
```

검증 범위: 비로그인 모집 조회·실시간 수신·삭제 이벤트·쓰기 거절·파티/초대 비노출, 잘못된 토큰 거절, 인증/등록, 공개 식별자와 닉네임만 노출, 파티 권한 재검사, 방장 초대, 지정 대상 수락, 만료·잠금·정원·강퇴·중복/재사용, 동시 수락, cursor, 메시지 중복 및 rate limit, 차단/신고/관리자 제재·삭제, 실제 WS 양방향 전달과 복원, 알림 실패 후 중복 방지, 보관 정리, 마이그레이션 재실행, 별도 활성화 설정 없이 REST·WS 사용, 신규 테이블 누락 시 기존 파티·마커 동작, 기존 위치·지도·파티·마커 회귀 테스트.

실제 운영 배포와 운영 프론트 smoke test는 별도로 수행한다. 로컬 테스트 통과를 운영 배포 완료로 간주하지 않는다.
