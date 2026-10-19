# 위치 찾기 WebSocket V3 복구 연동

## 변경 목적과 배포 범위

스크린샷 요청이 DB에 저장됐지만 지도까지 전달되지 않을 수 있는 기존 `/ws` 연결 관리를 교체한다. 프로그램 → 위치 API → Redis → 웹 `/ws` 경로이며 파티·모집 채팅 WebSocket과 별개다.

- 기존 URL `/ws?token=<기존 로그인 토큰>`과 로그인 인증을 유지한다.
- 기존 `init`, `message`, `wpf_location`, `wpf_log_location`, `wpf_raid_state`의 type과 payload 형식을 유지한다.
- 같은 계정의 여러 탭에 각각 전달한다. 한 탭 종료·전송 실패로 다른 탭의 구독을 정리하지 않는다.
- 구독 준비를 확인한 뒤 init을 보낸다. Redis 오류 시 구독을 재시도한다. Redis 클라이언트가 내부적으로 재구독한 경우에도 최신 위치 복원을 실행한다.
- 스크린샷/로그 위치 중 가장 최근 한 건은 Redis에 60초 동안 보관한다. 타이머 없는 레이드 상태도 60초이며, 유효 타이머가 있으면 종료 예정 시각 + 60초까지 보관한다. 최초 연결·재구독 시 복원한다. 프로그램에서 비활성 레이드 상태를 전송하면 최신 위치 캐시를 삭제한다.
- DB 마이그레이션과 신규 환경 변수는 없다. 기존 REDIS_HOST를 사용한다. legacy util/websocket.py는 보존하고 main.py와 위치 서비스에서 새 V3 구현으로 전환한다.

기존 프로그램은 API와 payload를 바꿀 필요가 없다. 백엔드만 배포해도 연결 종료 간섭 수정과 최신 위치 재전송은 적용된다. 프론트는 아래 추가 이벤트와 메타데이터를 반영한다. 운영 배포·실브라우저 검증은 별도로 수행한다.

## 프론트 요청 사항

1. **WebSocket open만으로 위치 수신 준비 완료를 표시하지 않는다.** 아래 `location_connection_status`의 ready를 받은 뒤 준비 완료로 표시한다. 구독 준비 전 프로그램이 보낸 위치는 최신 캐시가 남아 있으면 복원된다.
2. **reconnecting을 받으면 연결 복구 중으로 표시한다.** 이 경우 WebSocket 자체는 열려 있을 수 있다. 서버가 Redis를 재구독하므로 별도 WebSocket을 중복 생성하지 않는다. ready를 받으면 정상 상태로 복귀한다.
3. **WebSocket close/error에는 지수 backoff와 jitter로 재연결한다.** 예: 1·2·4·8·최대 30초. 인증이 만료됐다면 기존 로그인 토큰 갱신 절차를 사용한다. 페이지 내 연결을 재사용하고 언마운트 시 타이머와 소켓을 정리한다. 기존 keep-alive 동작을 유지한다.
4. **복원 위치도 기존 위치 처리기로 전달한다.** 추가 필드 때문에 패킷을 거부하지 않는다. 복원 위치는 이미 지난 관측이며 현재 연속 추적 위치처럼 표시하지 않는다. 지도·레이드가 맞는지 기존 검사를 유지한다. `wpf_log_location.payload.observed_at`이 있으면 실제 관측 시각으로 사용한다.
5. **중복과 순서를 처리한다.** event_id가 있으면 중복 적용을 막는다. 위치 두 종류와 레이드 상태를 합쳐 received_at_unix_us가 마지막 적용값보다 작은 이벤트를 무시한다. 메타데이터가 없는 기존 이벤트도 처리한다. 새 계정으로 전환하면 중복·순서 상태와 지도 위치를 초기화한다.
6. **오류 문구를 연결과 전송 단계에 맞춘다.** ‘위치 연결 복구 중’, ‘웹페이지 연결이 끊겼습니다’ 등으로 표시하고 메시지 전송 제한 문구를 재사용하지 않는다.

## 추가 이벤트

```json
{
  "type": "location_connection_status",
  "status": "ready",
  "connection_id": "연결 UUID"
}
```

status는 `ready` 또는 `reconnecting`이다. 구독 복구 후 같은 connection_id로 ready가 다시 올 수 있다. Redis 라이브러리가 내부 복구한 경우 중간 reconnecting 없이 ready만 다시 올 수도 있다. connection_id는 탭 연결마다 다르며 진단용이다.

첫 연결의 일반적인 순서는 `init` → 최신 레이드 상태·위치 복원(있을 때, 발행 시각 순) → `ready` → 실시간 이벤트다. ready 전에 들어오는 복원 위치도 처리한다. 연결 처리 실패·전송 지연 등으로 서버가 연결을 종료할 때 1013이 올 수 있다. 인증 오류는 기존 동작을 유지한다.

## 위치 이벤트의 추가 필드

```json
{
  "type": "wpf_location",
  "payload": "기존 위치 문자열 그대로",
  "event_id": "이벤트 UUID",
  "request_id": 12345,
  "received_at_unix_us": 1792148400000000,
  "replayed": false
}
```

| 필드 | 의미 |
|---|---|
| event_id | 같은 발행 이벤트는 모든 탭·복원에서 같은 ID를 사용 |
| request_id | 스크린샷 위치의 user_location_request.id. 로그 위치·레이드 상태에는 null |
| received_at_unix_us | Redis 발행 시각, Unix epoch 마이크로초. JS 표시용 밀리초는 /1000. 스크린샷을 실제 촬영한 시각과 다를 수 있음 |
| replayed | 캐시에서 복원하면 true, 실시간 전달이면 false |

`wpf_log_location`과 `wpf_raid_state`도 기존 payload를 유지하고 같은 메타데이터를 추가한다. 레이드 상태도 캐시가 유효하면 복원하며 프로그램이 `is_active:false`를 보내면 최신 위치 캐시를 지운다. 일반 알림은 기존 `{ "type": "message", "data": ... }` 형식을 유지한다. init의 밀린 일반 알림은 기존처럼 Redis 큐에서 소비하므로 모든 탭에 같은 과거 알림 목록이 보장되지는 않는다.

## 복구 범위와 진단

- 60초를 넘긴 위치나 서버 업데이트 전 이벤트는 복원을 보장하지 않는다. Redis 자체가 데이터를 잃거나 위치 API의 Redis 발행이 실패한 경우도 캐시로 복구하지 못한다.
- HTTP 200이나 DB 행이 있다는 사실은 지도 표시 완료를 뜻하지 않는다. 기존 API는 실패도 본문 msg=FAIL로 반환할 수 있으므로 프로그램에서는 HTTP 상태만 확인해서는 안 된다.
- 이번 변경에는 프론트 수신 확인(ACK)을 추가하지 않았다. 전송 로그는 서버의 소켓 전송 완료이며 지도 렌더 완료는 아니다.
- 문제 제보 시 발생 시각(KST), connection_id, event_id, request_id, 브라우저 연결 상태, 프로그램 버전을 함께 수집한다. 로그인 토큰·전체 WebSocket URL은 공유하지 않는다.

서버 로그는 `location_stored request_id=...` → `location_published event_id=... request_id=... subscribers=... pid=...` → `location_forwarded connection_id=... event_id=... replayed=... pid=...` 순서로 확인한다. subscribers는 Redis 구독 수이며 브라우저 표시 성공 수가 아니다.

## 프론트 검증

- 같은 계정으로 탭 두 개를 열어 둘 다 위치를 받고, 한 탭을 닫은 후 나머지 탭이 계속 받는지 확인한다.
- 새 연결을 연 직후 이전 연결을 닫아도 새 연결이 살아 있는지 확인한다.
- 위치 전송 직후 페이지를 새로고침하면 최근 위치가 복원되는지 확인한다.
- Redis 단절·복구 시 상태 안내가 바뀌고, 복구 후 새 위치를 받는지 확인한다.
- 레이드 종료 후 이전 위치를 복원하지 않는지, 로그 위치·일반 알림이 기존대로 처리되는지 확인한다.

타이머 필드·캐시 연장·만료 처리의 최신 규격은 [리뉴얼 데스크톱 백엔드 규격](where_am_i_desktop_v3_backend.ko.md)을 따른다.
