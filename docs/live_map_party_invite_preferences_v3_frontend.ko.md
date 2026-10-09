# V3 파티 초대 수신 설정 및 남용 방지 — 프론트 연동

작성일: 2026-10-09. URL은 `API_PREFIX=/api` 기준이다. 기존 모집 채팅·접속자 목록·초대 API를 확장한다.

## 수신 설정 UI

로그인 사용자에게 ‘파티 초대 받기’ 토글을 표시한다. 기본값은 `true`이며 계정별로 저장된다. 비로그인은 설정 API를 사용할 수 없다. 토글을 끄더라도 접속자 목록에서 숨기지 않는다.

아래 API는 `Authorization: Bearer <Google access token>`이 필요하다. 본인 설정만 조회·변경하며 요청에 사용자 ID를 보내지 않는다.

| 메서드 / URL | 요청 | 성공 응답 data |
|---|---|---|
| GET `/api/live-map/v3/chat/me/party-invite-preferences` | 없음 | `{allow_party_invites: boolean}` |
| PUT `/api/live-map/v3/chat/me/party-invite-preferences` | `{allow_party_invites: boolean}` | `{allow_party_invites: boolean}` |

설정 변경 예시:

```json
{"allow_party_invites": false}
```

```json
{"status": 200, "msg": "OK", "data": {"allow_party_invites": false}}
```

문자열 `"false"`, 숫자, 추가 필드는 422다. 실패 시 기존 토글 상태를 유지하거나 서버 설정을 다시 조회한다. 응답은 `Cache-Control: private, no-store`다.

수신을 끄면 해당 사용자가 **받은 모든 저장된 pending 초대**를 같은 트랜잭션에서 `revoked`로 변경한다. 알림 수에서 제외하고 다시 켜도 복구하지 않는다. 사용자가 보낸 초대는 취소하지 않는다. 다시 켠 이후에는 새 초대를 받을 수 있다.

## 초대 버튼과 서버 검증

기존 `GET /api/live-map/v3/chat/users/{user_id}/actions?room_id=<UUID>`를 사용한다. 기존 필드에 `retry_after: number|null`이 추가된다.

```json
{
  "status": 200,
  "msg": "OK",
  "data": {
    "user": {"id": "<공개 사용자 UUID>", "nickname": "파티원"},
    "blocked": false,
    "can_block": true,
    "can_restrict": false,
    "can_invite": false,
    "invite_disabled_reason": "PARTY_INVITATION_REJECT_COOLDOWN",
    "retry_after": 580,
    "member_id": null,
    "can_unkick": false
  }
}
```

`can_invite=false`이면 버튼을 비활성화하고 `invite_disabled_reason`에 맞는 안내를 표시한다. 시간 제한이면 초 단위 `retry_after`로 재조회 시간을 정한다. 값이 null이면 시간 제한 안내를 표시하지 않는다. 방이 없으면 기존 `PARTY_ROOM_REQUIRED`, 방장이 아니면 기존 권한 오류가 적용된다.

사용자 액션 조회는 해당 시점의 안내다. 설정 변경·다른 탭 요청·초대 거절 등에 따라 결과가 바뀔 수 있으므로 실제 `POST /api/live-map/v3/party-invitations` 실패도 반드시 처리한다. 서버는 동일한 수신 설정·차단·시간 제한·중복 여부를 검사한다.

| 사유 코드 | 초대 생성 HTTP | 표시 문구 예시 |
|---|---|---|
| `PARTY_INVITATIONS_UNAVAILABLE` | 403 | 상대방이 현재 파티 초대를 받을 수 없습니다. |
| `PARTY_INVITATION_DUPLICATED` | 409 | 이미 대기 중인 초대가 있습니다. |
| `PARTY_INVITATION_REJECT_COOLDOWN` | 429 | 초대가 거절되어 잠시 후 다시 초대할 수 있습니다. |
| `PARTY_INVITATION_RATE_LIMITED` | 429 | 초대를 너무 자주 보냈습니다. 잠시 후 다시 시도해주세요. |
| `PARTY_INVITATION_LIMIT` | 429 | 상대방에게 대기 중인 초대가 많습니다. 잠시 후 다시 시도해주세요. |

기존 자기 초대·잠금·방 종료·정원 초과·이미 참여·강퇴·방장 권한 오류도 유지한다. `PARTY_INVITATIONS_UNAVAILABLE`은 **수신 해제와 수신자의 발신자 차단에 공통으로 사용**한다. 프론트는 이 코드로 ‘상대가 나를 차단했다’고 표시하거나 추측하지 않는다. `blocked` 필드는 기존처럼 내가 상대를 차단했는지만 의미한다.

시간 제한 응답에는 기존 `Retry-After` 헤더와 함께 `data.retry_after`가 정수 초로 전달된다.

```json
{
  "status": 429,
  "msg": "PARTY_INVITATION_REJECT_COOLDOWN",
  "data": {"retry_after": 600}
}
```

시간 제한이 없는 일반 오류의 `data`는 기존처럼 null이다. 검증 오류는 `data.errors`를 사용한다.

## 초대 남용 방지 정책

- 동일 발신자→동일 수신자의 유효한 pending 초대는 방을 바꿔도 중복 생성하지 않는다. 기존 같은 방→같은 수신자의 중복 제한도 유지한다.
- 수신자가 거절하면 해당 발신자→수신자 조합에 **거절 시각부터 600초** 동안 재초대를 제한한다. 방을 바꿔도 적용된다. 다른 발신자에게는 적용하지 않는다.
- 발신자별 **직전 60초의 성공한 초대 생성은 최대 3건**이다. 방·수신자를 바꿔도 합산한다. 실패 요청은 생성 건수에 포함하지 않는다. 초대를 취소·거절해도 이미 생성한 건수는 차감하지 않는다.
- 두 시간 제한이 함께 적용될 수 있다. 안내된 대기 시간이 끝나면 액션 API를 재조회한다.
- 수신자가 발신자를 차단하면 새 초대를 거부한다. 발신자가 수신자를 차단한 방향만으로는 수신자의 초대 수신 설정을 바꾸지 않는다.
- 서버는 PostgreSQL 계정 행 잠금과 DB 시각을 사용한다. 여러 탭·서버의 동시 요청에도 생성/수신 설정/차단/거절 검사가 직렬화된다.

## WebSocket과 다른 탭 동기화

기존 `/api/live-map/v3/chat/ws` 연결과 30초 heartbeat를 그대로 사용한다. 로그인 snapshot에 본인 설정이 추가된다.

```json
{
  "type": "snapshot",
  "event_id": "<UUID>",
  "server_time": "<ISO-8601>",
  "data": {
    "party_invite_preferences": {"allow_party_invites": true}
  }
}
```

위 snapshot은 추가 필드만 발췌했다. 기존 메시지·초대·알림·접속자 목록 필드도 유지된다. 게스트의 `party_invite_preferences`는 null이다.

본인 설정 변경은 로그인된 본인의 모든 채팅 연결에 다음 이벤트로 전달된다. 다른 사용자나 게스트에게 본인 설정 이벤트를 보내지 않는다.

```json
{
  "type": "party_invite_preferences_updated",
  "event_id": "<UUID>",
  "server_time": "<ISO-8601>",
  "data": {"allow_party_invites": false}
}
```

이 이벤트와 snapshot 수신 시 토글 상태를 서버 값으로 교체한다. 설정 이벤트의 data에는 상대 사용자 설정이나 차단 관계가 포함되지 않는다.

수신 해제로 취소된 초대는 기존 `party_invitation_updated` 이벤트로 전달하며 초대 객체에 다음 상태가 추가된다.

```json
{"id": "<초대 UUID>", "status": "revoked", "status_reason": "receiver_unavailable"}
```

위 예시는 초대 객체의 변경 필드만 발췌했다. 기존 inviter/party/expires_at 등의 전체 객체를 계속 전달한다. 수신자와 발신자에게 전달하며 ‘초대가 취소되었습니다’ 또는 ‘수신 불가로 취소되었습니다’로 표시한다. 이 상태의 초대에서는 수락·거절 버튼을 숨긴다. TypeScript의 status_reason 유니온에 `receiver_unavailable`을 추가한다.

본인의 `party_notifications_updated` 이벤트도 다시 적용한다. 이번에 꺼진 사용자의 incoming pending count는 0이다. 설정·초대·알림 이벤트의 순서는 가정하지 않는다. 초대는 ID 기준으로 갱신하고 설정/알림은 전체 서버 값으로 교체한다. 동일 상태 이벤트가 다시 올 수 있으므로 처리는 멱등하게 한다. 발신자의 초대 메뉴가 열려 있으면 취소 이벤트를 받은 뒤 액션 API를 재조회한다.

이벤트는 DB commit 이후 발행한다. 발행 실패 시 설정 변경 자체는 성공하며 REST의 `X-Chat-Realtime: unavailable`로 알린다. 약 2초 주기의 상태 확인과 heartbeat snapshot으로 설정·초대·알림을 복구한다. 재접속 시 새 snapshot을 적용한다.

## 배포와 설정값

백엔드 배포 전에 V3 DB에 `sql/migrations/20261009_party_invite_preferences_v3.sql`을 적용한다. 기존 채팅 테이블과 초대 status_reason 컬럼이 있는 환경을 전제로 한다. 새 설정 테이블·인덱스를 추가하고 사유 CHECK에 `receiver_unavailable`을 허용한다. 기존 초대·계정 데이터는 유지하며 반복 실행할 수 있다. 별도로 운영 DB 전체에 `platform_db.sql`을 재실행하지 않는다.

설정 행이 없는 기존 계정은 수신 허용으로 동작한다. 시간 제한 값은 모든 서버에 같은 환경변수로 지정한다. 값은 양의 정수다.

| 환경변수 | 기본값 | 의미 |
|---|---|---|
| `V3_PARTY_INVITE_SENDER_LIMIT` | 3 | 발신자 생성 건수 |
| `V3_PARTY_INVITE_WINDOW_SECONDS` | 60 | 생성 건수 계산 구간(초) |
| `V3_PARTY_INVITE_REJECTION_COOLDOWN_SECONDS` | 600 | 거절 후 재초대 제한(초) |

## 프론트 확인 항목

1. 기본 수신 허용 상태를 조회하고 끄기/켜기가 새로고침 뒤에도 유지되는지 확인한다.
2. 수신 해제 시 받은 pending 초대가 취소되고 알림 수가 0이 되는지 확인한다. 다시 켜도 취소 초대는 복구하지 않는다.
3. 같은 계정의 다른 탭에서도 토글·초대·알림이 갱신되는지 확인한다.
4. 수신을 끈 사용자가 접속자 목록에는 계속 표시되는지 확인한다.
5. 거절 후 같은 발신자가 다른 방에서 초대해도 10분 제한을 받는지 확인한다.
6. 1분 안에 네 번째 성공 초대를 만들려고 하면 429와 retry_after를 받는지 확인한다.
7. 수신자 차단과 수신 해제의 발신자 안내가 같고 차단 관계가 노출되지 않는지 확인한다.
8. 동시에 요청해도 동일 상대 중복이나 발신자 3건 제한을 우회하지 못하는지 확인한다.

전체 채팅 계약: [live_map_chat_v3_api.ko.md](live_map_chat_v3_api.ko.md).
