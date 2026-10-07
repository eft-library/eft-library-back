# 내 위치 찾기·파티·모집 프론트 연동 변경

모든 경로는 `/live-map` 기준이며, 아래 REST API는 로그인 필수다.
응답은 기존 `{status, msg, data}` 형식을 유지한다. DB는 기존 `platform_db.sql`의
V3 테이블을 사용한다. 이번 변경에 추가 DB 마이그레이션은 없다.

## 관리자 밴

밴은 기존 채팅 제한 기능을 사용한다. 모집·파티 채팅의 새 메시지 전송을 막는다.
지도 위치 공유, 파티 입장, 계정 로그인까지 차단하는 기능은 아니다.

- `PUT /live-map/v3/chat/admin/restrictions/{user_id}`: 관리자만 가능.
  요청 `{ "reason": "도배", "expires_at": null }`은 영구 채팅 밴이다.
  기간 제한은 미래의 시간대 포함 ISO8601 시각을 `expires_at`에 전달한다.
- `DELETE /live-map/v3/chat/admin/restrictions/{user_id}`: 관리자만 밴 해제 가능.
- **추가** `GET /live-map/v3/chat/admin/restrictions?limit=50&offset=0`:
  현재 유효한 밴 목록. 각 항목은 `{user:{id,nickname},reason,expires_at,create_time}`.
  만료된 제한은 제외하며 이메일은 노출하지 않는다.
- **추가** `GET /live-map/v3/chat/me/moderation`:
  본인 상태 `{is_admin,restricted,reason,expires_at}`.

WebSocket `snapshot.data.moderation`에도 본인 상태를 제공한다.
변경·만료 시 `chat_moderation_updated` 이벤트로 같은 객체를 전달한다(통상 2초 내).
밴 상태에서도 읽기 연결은 유지하고 메시지 입력을 비활성화한다.
서버는 전송 시에도 권한을 검사하고 `403 CHAT_RESTRICTED`를 반환한다.

## 닉네임 상호작용

**추가** `GET /live-map/v3/chat/users/{user_id}/actions?room_id={room_id}`.
`user_id`는 채팅 메시지의 `user.id`이며 파티 `member_id`와 다르다.

응답 필드:

| 필드 | 용도 |
| --- | --- |
| `user` | `{id,nickname}` |
| `blocked`, `can_block` | 차단/해제 메뉴 표시. 본인 차단 불가 |
| `can_restrict` | 관리자 밴 메뉴 표시 |
| `can_invite`, `invite_disabled_reason` | 초대 가능 여부와 불가 사유 |
| `member_id`, `can_unkick` | 강퇴 해제 대상과 메뉴 표시 |

`room_id` 생략 시 파티 관련 정보는 제공하지 않고 불가 사유는 `PARTY_ROOM_REQUIRED`다.
`room_id` 지정 조회는 해당 방의 현재 방장만 가능하다(그 외 403).
메뉴 상태는 조회 시점 기준이며 실제 작업 API에서 다시 권한·방 상태를 검사한다.
닉네임 메뉴의 크기·위치와 초록 아이콘 이동은 프론트에서 적용한다.

## 강퇴 해제와 재초대

`DELETE /live-map/v3/party/rooms/{room_id}/members/{member_id}/kick`.
현재 방장만 사용 가능하며 기존 `PartySnapshotV3`를 반환한다.

강퇴 해제는 멤버의 `kicked` 상태를 `left`로 바꾼다. 자동 입장시키지 않고 정원도
늘리지 않는다. 새 초대 수락 또는 올바른 비밀번호 입장이 필요하다.
해제된 대상에 반복 호출하면 성공하며 현재 참여 중인 대상은 `409 MEMBER_NOT_KICKED`다.
존재하지 않거나 다른 방의 멤버는 404다. 기존 파티 실시간 변경 알림도 발행된다.

강퇴 상태에서 초대하면 기존 `403 PARTY_MEMBER_KICKED`를 유지한다.
이 코드는 프론트에서 **“강퇴된 사용자입니다. 강퇴를 해제한 뒤 다시 초대해주세요.”**로
표시한다. actions 조회에도 같은 `invite_disabled_reason`과 `can_unkick=true`를 제공한다.
강퇴 해제 후 새 초대를 생성해야 하며, 이전 입장 전에 발급된 초대는 다시 유효해지지 않는다.

## 파티 초대 알림

**추가** `GET /live-map/v3/party-invitations/notifications`:

```json
{"status":200,"msg":"OK","data":{"party_invitation_count":1,"notification_tab":"party"}}
```

`party_invitation_count`는 **본인이 받은 유효한 pending 초대** 개수다.
본인이 보낸 초대, 만료·처리·취소된 초대, 종료/정원 초과 방 또는 강퇴/이미 참여 상태로
무효화된 초대는 제외한다. 읽었다는 이유로 개수를 줄이지 않으며 수락·거절 등으로 줄인다.
방 잠금은 초대를 취소하지 않으므로 잠긴 방의 대기 초대는 개수에 남는다.

WebSocket `snapshot.data.notifications`에 같은 객체를 포함하고 개수 변경 시
`party_notifications_updated` 이벤트로 전달한다(통상 2초 내).
게스트 snapshot의 개수는 0이다. 모든 초대 응답·초대 이벤트에도
`notification_tab: "party"`를 추가했다.

프론트는 이 개수를 **파티 탭 배지**에만 사용한다. 기존 초대 목록에는 받은 초대와
보낸 초대가 함께 있으므로 배열 길이를 배지 개수로 사용하지 않는다.
모집 메시지의 읽지 않은 개수는 별도로 관리한다. 재접속/heartbeat snapshot 또는
위 REST API로 배지와 밴 상태를 복구할 수 있다.
