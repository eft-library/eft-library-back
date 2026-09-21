# Live Map 파티 V3 테이블 설계안

상태: 테이블 정의, REST API, WebSocket 및 연결 유예 후 자동 정리 구현 완료.
현재 동작은 `live_map_party_v3_api.md`와 `live_map_party_v3_websocket.md` 참고.
기준: `platform_db.sql`. 기존 live map/레거시 테이블은 수정하지 않는다.
새 모델·서비스·쿼리는 V3 명명 규칙과 `V3Database`를 사용한다.

## 기능 범위

- 방 목록은 공개하고 모든 방은 비밀번호로 입장한다.
- 목록에는 방 ID, 이름, 맵, 현재 인원, 정원, 입장 잠금 여부만 공개한다.
- 방 내부에서 참여자 색상, 일시적인 핑, 지속되는 마커를 공유한다.
- 첫 버전은 방 생성 시 선택한 맵을 고정한다. 다른 맵은 새 방으로 만든다.
- 방명은 중복 허용한다. 목록에 짧은 방 ID를 함께 표시해 구분한다.
- 방 생성과 참여 모두 사이트 로그인이 필수다. 인증된 계정 이메일로 참여자를 식별한다.

## 기존 스키마와의 연결

- 맵: `maps.id` (`text`). `maps.parent_map_id`로 상위/하위 맵을 구분한다.
- 층: `live_map_floors.id` (`text`), 소속 맵은 `live_map_floors.map_id`.
- 좌표: 기존 live map과 같은 `x`, `z` (`numeric`). 화면 픽셀이나 위경도로 저장하지 않는다.
- 계정: `user_info.email` (`text`, PK). 존재하지 않는 user ID를 가정하지 않는다.
- 현재 맵 선택 쿼리는 `coalesce(m.parent_map_id, m.id)`를 표시용 맵으로 사용한다.
  따라서 마커 층의 맵 ID와 방의 맵 ID가 항상 같다고 가정하면 안 된다.

## 1. live_map_party_rooms — 방

| 필드 | 타입 | 제약 / 의미 |
| --- | --- | --- |
| id | uuid | PK, 애플리케이션에서 생성 |
| name | varchar(60) | NOT NULL, 공백만 있는 값 금지 |
| map_id | text | NOT NULL, FK → maps.id, 삭제 RESTRICT |
| password_hash | text | NOT NULL, 평문 저장 금지, 응답에 포함 금지 |
| is_locked | boolean | NOT NULL DEFAULT false, 신규 입장 잠금 |
| max_members | smallint | NOT NULL, 양수; 초기 기본 정원은 제품 정책으로 확정 |
| empty_since | timestamptz | NULL 허용, 접속자가 0명이 된 시간 |
| closed_at | timestamptz | NULL이면 열린 방, 값이 있으면 종료된 방 |
| create_time | timestamptz | NOT NULL DEFAULT now() |
| update_time | timestamptz | NOT NULL DEFAULT now(), 변경 시 서비스에서 갱신 |

인덱스 제안:

- `(create_time DESC, id) WHERE closed_at IS NULL`: 목록 페이지 조회.
- `(map_id, create_time DESC, id) WHERE closed_at IS NULL`: 맵 필터.
- `(empty_since) WHERE closed_at IS NULL AND empty_since IS NOT NULL`: 빈 방 정리.
- 방 이름 부분 검색이 필요하면 `name gin_trgm_ops` GIN 인덱스 추가.
  `pg_trgm` 확장은 현재 스키마에 선언되어 있다.

공개/비공개 컬럼은 두지 않는다. 모든 방에 동일한 입장 정책을 적용한다.
현재 인원은 접속 상태에서 계산하고 별도 카운터 컬럼으로 중복 저장하지 않는다.

## 2. live_map_party_members — 참여자와 방 내 권한

| 필드 | 타입 | 제약 / 의미 |
| --- | --- | --- |
| id | uuid | PK, 애플리케이션에서 생성 |
| room_id | uuid | NOT NULL, FK → live_map_party_rooms.id, 삭제 CASCADE |
| user_email | text | NOT NULL, FK → user_info.email, 삭제 RESTRICT |
| nickname | varchar(30) | NOT NULL, 방에서 표시할 이름, 공백만 있는 값 금지 |
| color | varchar(7) | NOT NULL, `#RRGGBB` 형식, 서비스에서 대문자로 정규화 |
| role | text | NOT NULL, CHECK: owner / member |
| status | text | NOT NULL, CHECK: joined / left / kicked |
| joined_at | timestamptz | NOT NULL DEFAULT now(), 최근 입장 시 갱신 |
| left_at | timestamptz | joined이면 NULL, left/kicked이면 NOT NULL |
| create_time | timestamptz | NOT NULL DEFAULT now() |
| update_time | timestamptz | NOT NULL DEFAULT now(), 변경 시 갱신 |

제약 / 인덱스 제안:

- `UNIQUE (room_id, id)`: 마커 작성자가 같은 방 사람인지 복합 FK로 검증.
- `UNIQUE (room_id, user_email)`: 로그인 계정은 방마다 하나의 참여자 행을 재사용.
- `UNIQUE (room_id) WHERE role = 'owner' AND status = 'joined'`: 방장 최대 1명.
- `UNIQUE (room_id, color) WHERE status = 'joined'`: 참여 중인 사람끼리 색상 구분.
- `(room_id, status)`: 방 참여자 및 강퇴 상태 조회.
- `(user_email)`: 계정별 참여 방 조회 및 계정 삭제 처리.

`joined`는 입장 자격을 뜻하며 WebSocket이 연결됐다는 뜻은 아니다.
일시적인 연결 끊김으로 `left`로 바꾸지 않는다.
탈퇴/강퇴해도 행을 남겨 마커 작성자와 강퇴 상태를 유지한다.
계정 삭제 시 FK는 RESTRICT로 두고, 소유 방의 양도/종료, 해당 계정이 작성한 마커 삭제,
참여자 삭제를 서비스 트랜잭션에서 처리한 다음 계정을 삭제한다.
이는 후속 계정 삭제 흐름과 연동할 사항이다.

`user_email`은 클라이언트가 보내는 값을 신뢰하지 않고 로그인 인증 결과에서 가져온다.
닉네임은 표시용이며 계정 이메일을 다른 참여자나 공개 목록에 노출하지 않는다.
재접속은 로그인 계정과 해당 방의 참여 상태를 확인한다. 별도 게스트 토큰은 필요 없다.

## 3. live_map_party_markers — 지속되는 공유 마커

| 필드 | 타입 | 제약 / 의미 |
| --- | --- | --- |
| id | uuid | PK, 애플리케이션에서 생성 |
| room_id | uuid | NOT NULL, FK → live_map_party_rooms.id, 삭제 CASCADE |
| created_by_member_id | uuid | NOT NULL, 아래 복합 FK 적용 |
| floor_id | text | NOT NULL, FK → live_map_floors.id, 삭제 RESTRICT |
| x | numeric | NOT NULL, 기존 live map 좌표계의 유한 값 |
| z | numeric | NOT NULL, 기존 live map 좌표계의 유한 값 |
| marker_type | text | NOT NULL, CHECK: normal / danger / rally / target |
| label | varchar(100) | NULL 허용, 짧은 설명 |
| version | integer | NOT NULL DEFAULT 1, 양수, 동시 수정 충돌 검출 |
| create_time | timestamptz | NOT NULL DEFAULT now() |
| update_time | timestamptz | NOT NULL DEFAULT now(), 변경 시 갱신 |

- 복합 FK `(room_id, created_by_member_id)` → live_map_party_members `(room_id, id)`.
  참여자 단독 삭제는 NO ACTION, 방 전체 삭제 시에는 방의 CASCADE로 함께 정리한다.
- `(room_id, floor_id, id)`: 입장/재접속 시 마커 목록 조회.
- `(room_id, created_by_member_id)`: 작성자별 마커 조회.
- `(floor_id)`: 층 FK 확인 및 관리.
- 맵은 방과 층으로 알 수 있으므로 마커에 `map_id`를 중복 저장하지 않는다.
- 마커 생성/층 변경 시 `floor.map_id = room.map_id` 또는
  해당 층 맵의 `parent_map_id = room.map_id`인지 V3 서비스에서 검증한다.
  기존 테이블 구조를 변경하지 않는 설계이므로 이 관계는 단순 FK만으로 보장되지 않는다.
- 마커 편집은 작성자와 방장에게 허용하는 안을 기본으로 한다.
  `version` 일치 조건으로 수정 후 증가시켜 오래된 요청의 덮어쓰기를 막는다.

## 실시간 데이터의 저장 경계

| 데이터 | 저장/전달 방식 제안 |
| --- | --- |
| 방, 참여 권한, 지속 마커 | PostgreSQL |
| 몇 초 후 사라지는 핑 | WebSocket 이벤트, expires_at 포함, DB 저장하지 않음 |
| 현재 접속자 | Redis의 연결별 TTL, 참여자별 중복 제거하여 인원 계산 |
| 수동으로 찍는 현재 위치 | Redis TTL로 참여자당 최신 floor_id/x/z 유지 |
| 비밀번호 연속 실패 횟수 | Redis TTL로 요청자·방 기준 제한 |
| 여러 서버 간 방 이벤트 전달 | Redis Pub/Sub → 각 서버 WebSocket |

현재 저장소에 Redis/WebSocket 사용 코드가 있으나 파티용 구현은 별도 V3로 추가한다.
재접속 시 DB 마커 스냅샷과 유효한 현재 위치를 받고, 이미 만료된 핑은 복원하지 않는다.
순간 핑/현재 위치에도 방 참여 자격과 층 소속 검증을 동일하게 적용한다.

## 트랜잭션과 방 수명

1. 방 생성과 owner 참여자 생성을 하나의 트랜잭션으로 수행한다.
   부분 유니크 제약은 방장 최대 1명만 보장하므로 열린 방의 방장 존재는 서비스가 보장한다.
2. 입장/재입장 시 방 행을 잠그고 종료·잠금·강퇴·비밀번호·정원을 확인한다.
   정원은 joined 참여자 기준으로 제한한다. 접속 해제 후 유예 시간 동안 자리를 유지하고,
   유예 시간이 지나면 left로 전환한다. 온라인 인원과 예약 중인 자리는 구분한다.
3. 방장 퇴장/유예 만료 시 다른 joined 참여자에게 양도하거나 방을 종료한다.
   기존 owner를 member로 바꾸고 새 owner를 지정하는 과정을 같은 트랜잭션으로 처리한다.
4. 강퇴는 status 변경과 소켓 종료를 함께 처리한다. 이후 재접속과 모든 변경 요청에서도
   상태를 다시 확인한다. 비밀번호를 다시 입력해도 kicked 계정은 재입장할 수 없다.
5. 접속자가 없으면 empty_since를 기록하고, 재접속하면 지운다.
   정리 작업은 방 행을 잠그고 최신 접속 상태를 재확인한 뒤 종료한다.
   TTL 유실/서버 재시작 이후 접속 상태를 재조정하는 작업도 필요하다.
6. 종료 방은 목록/입장/변경 요청에서 제외한다. 보존 기간 뒤 방을 삭제하면
   참여자와 마커도 함께 삭제한다. 유예 시간·빈 방 종료 시간·보존 기간은 설정으로 둔다.

## 현재 정책과 후속 항목

- REST API 기본 정원은 5명, 최대 10명이며 기본 색상 팔레트는 10개다.
- 명시적 마지막 퇴장은 즉시 종료한다. WebSocket lease는 45초, 연결 복구 유예는 90초다.
  자동 퇴장과 방장 양도/빈 방 종료는 15초 주기의 배치 작업이 수행한다.
  종료 기록의 보존 기간 및 물리 삭제 스케줄러는 별도 정책 확정 후 구현한다.
- `platform_db.sql`에 신규 테이블 정의를 추가했고 사용자가 DB 적용을 완료했다.
