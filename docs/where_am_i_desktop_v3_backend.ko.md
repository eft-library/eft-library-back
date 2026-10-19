# 리뉴얼 데스크톱 API: 백엔드 구현·연동 규격

기준 문서: 인접 `eft-library-where-am-i/docs/BACKEND_API_REQUIREMENTS.md` (2026-10-19).
이번 변경은 백엔드 구현과 격리 테스트까지다. 클라이언트·웹 코드와 운영 DB/API는 변경하지 않았다.

## 1. 레이드 타이머

`POST /api/where-am-i/v3/send-raid-state` 경로와 email 기반 기존 사용자 확인을 유지한다. 기존 클라이언트처럼 추가 필드를 생략하거나 타이머 없이 Woods·Customs·Shoreline 상태를 보내도 정상 수신한다.

추가 nullable 필드:

| 필드 | 규칙 |
|---|---|
| session_id | 64자리 소문자 16진수. 생략·null 허용. 인증 정보가 아님 |
| timer_observed_at | 시간대 포함 ISO 8601, UTC로 정규화 |
| raid_ends_at | 시간대 포함 ISO 8601, UTC로 정규화 |

두 시간 필드는 함께 유효하거나 둘 다 null이어야 한다. 시간이 있으면 활성 상태, 지원 map slug, started_at, session_id가 필수이며 종료는 관측 시각보다 뒤여야 한다. started_at도 값이 있다면 시간대가 필요하다. 타이머가 없어도 정상 상태로 처리하며 35분 등 기본 길이를 만들어 넣지 않는다.

정상 응답은 HTTP 200, `{ "status": 200, "msg": "OK", "data": true }`다. 이 응답은 Redis 상태 저장·발행 완료이며 특정 브라우저의 지도 표시 완료가 아니다.

| HTTP | detail | 의미 |
|---|---|---|
| 422 | FastAPI 검증 detail 배열 | 부분 시간, 시간대 누락, 역전된 시간, 잘못된 session_id/타이머 맥락 |
| 404 | USER_NOT_FOUND | 등록되지 않은 email |
| 409 | RAID_TIMER_EXPIRED | Redis 처리 시각에 종료 예정 시각이 이미 지남 |
| 409 | RAID_STATE_STALE | 아래 순서 정책으로 명확하게 이전 상태임을 확인 |
| 503 | RAID_STATE_DATABASE_UNAVAILABLE | 사용자 확인 DB 실패 |
| 503 | RAID_STATE_PUBLISH_UNAVAILABLE | Redis 저장·발행 실패 |

구조 검증 실패와 저장 실패를 data:true로 반환하지 않는다. DB나 Redis가 실패해도 클라이언트의 감시 기능 자체를 중단하는 정책은 추가하지 않는다.

### 개인 WebSocket과 복원

기존 `/ws?token=...` 개인 채널의 `wpf_raid_state.payload`에 session_id·timer_observed_at·raid_ends_at을 포함하고 email은 제외한다. 기존 type·payload 구조와 event_id·received_at_unix_us·replayed 등 메타데이터를 유지한다. 같은 맵·started_at에서도 타이머가 늦게 추가되면 새 이벤트로 발행한다.

- 유효한 타이머 상태의 캐시 TTL은 Redis 시각 기준 `ceil(raid_ends_at - now) + 60초`다. 최초 전송 60초 후에도 아직 유효한 종료 시각을 복원한다.
- 타이머 없는 상태의 캐시는 기존 60초다. 새 null 스냅샷은 이전 상태에 병합하지 않고 전체를 교체한다.
- 새 세션·맵·시작 시각 전환이나 is_active:false 요청에서는 이전 위치 캐시를 정리한다. 새 세션에서 이전 자동 타이머가 섞이지 않는다.
- 보관 유예 60초 중 재연결한 경우 종료된 타이머 두 필드는 null로 전달한다. 세션 맥락은 유지하되 만료 타이머를 다시 활성화하지 않는다.
- 타이머는 PostgreSQL에 저장하지 않는다. Redis 손실이나 캐시 만료 후에는 없는 타이머를 복원하지 않는다.

### 여러 탭·클라이언트·재시도 순서 정책

Redis Lua 한 번으로 검증 → 상태 교체 → 캐시 TTL → 발행을 처리한다. 여러 워커에서 동시에 처리해도 검증과 교체 사이를 우회하지 않는다.

1. 양쪽 started_at이 확인될 때 더 이른 시작의 요청은 409로 거부한다.
2. 같은 session_id에서 양쪽 관측 시각이 확인될 때 더 이른 관측 타이머는 거부한다.
3. session_id 전환 시 이전 ID를 폐기 이력으로 남긴다. 이후 폐기된 ID의 재시도는 거부한다. 이력은 최근 최대 128개·24시간 범위의 보조 정보다. session_id의 해시 정렬로 순서를 판단하지 않는다.
4. 같은 상태 재시도는 정상 수신·재발행할 수 있다. 종료 예정 시각을 바꾸거나 현재 시각부터 새로 시작하지 않는다.
5. null 스냅샷은 현재 스냅샷의 타이머 없음으로 적용한다. started_at·관측 시각·식별 정보가 없어 순서를 확인할 수 없는 요청은 Redis 도착 순서로 처리한다. 구버전 클라이언트와 새 클라이언트를 동시에 같은 계정으로 쓰거나 복수 앱이 서로 다른 로딩 스냅샷을 보내는 경우 전역 순서는 보장하지 않는다.

서버 시계는 Redis 시각, 웹 표시 시계는 브라우저 시각을 사용한다. 운영에서 게임과 비교해 시계 오차를 확인해야 한다. 임의 보정값은 추가하지 않았다.

### 웹 후속 작업

이번 작업에서 웹 코드는 변경하지 않았다. 웹에서 nullable 필드를 허용하고, 같은 맵·활성·유효 타이머일 때 `max(0, raid_ends_at - 현재 UTC)`로 남은 시간을 계산한다. 같은 이벤트·재연결 때 전체 길이부터 재시작하지 않는다. 새 세션과 null 타이머에서 이전 자동 기준을 비우고 수동 입력 상태를 유지한다. Woods부터 실제 게임 시각과 BTR **예상** 표시를 검증한다. 실제 도착·정차 감지 기능으로 설명하지 않는다.

## 2. 버전 확인

`POST /api/where-am-i/v3/check-version`은 공개 조회이며 email·로그인 정보가 필요 없다.

```json
{"product":"where-am-i","current_version":"1.0.0.0","platform":"windows","architecture":"x64","channel":"stable"}
```

현재 지원 조합은 위 값들이다. 다른 조합·추가 필드는 422다. 버전은 최대 64자, 2~4개 숫자 구성으로 .NET Version의 Int32 범위에서 검증하며 빠진 구성은 0으로 비교한다. 사전 배포·metadata는 받지 않는다.

정상 응답의 data:

```json
{
  "current_version":"1.0.0.0",
  "latest_version":"1.1.0.0",
  "min_supported_version":"1.0.0.0",
  "update_available":true,
  "update_required":false,
  "download_url":"https://github.com/eft-library/eft-library-where-am-i/releases/tag/live-map-v2",
  "release_notes":"설명용 변경 내용"
}
```

위 버전과 URL은 설명용이다. 마이그레이션에서 실제 배포로 등록하지 않는다.

- 제품·플랫폼·아키텍처·채널이 맞고 is_active=true, published_at이 DB 현재 시각 이하인 배포만 조회한다.
- 문자열이 아닌 숫자 구성으로 최신 버전을 선택한다. 같은 숫자 의미의 버전은 published_at·id 순으로 결정한다.
- update_available은 current < latest, update_required는 current < min_supported이며 min_supported <= latest를 검증한다.
- 현재 버전이 최신보다 높아도 두 플래그는 false다. 업데이트 없음에 다운로드 URL null·빈 문자열을 허용한다.
- 업데이트가 있으면 HTTPS, 기본/443 포트, 사용자 정보 없는 공식 다운로드 URL이 필요하다. GitHub는 github.com/eft-library/eft-library-where-am-i/releases 및 그 하위 릴리스·asset 주소만 허용한다. 다른 저장소·issues·위장 호스트는 거부한다. 기존 eftlibrary.com·www.eftlibrary.com URL도 호환성을 위해 유지한다. 잘못된 URL은 저장 데이터 오류로 503이다. exe의 VersionCheckService 허용 목록도 함께 수정했으므로 수정된 exe를 빌드·배포해야 한다. 백엔드만 재배포하면 예전 exe는 GitHub 링크를 여전히 거부할 수 있다.
- release_notes는 nullable 일반 텍스트 최대 4000자다. HTML 렌더링을 지시하지 않는다.
- 공개된 대상이 없으면 404 DESKTOP_RELEASE_NOT_FOUND, DB 실패·잘못된 저장 메타데이터는 503 DESKTOP_METADATA_UNAVAILABLE이다. 최신 버전을 만들어 반환하지 않는다.
- 필수 업데이트는 정보 제공이다. 기존 감지·위치 API를 이 응답으로 차단하거나 실행 파일을 설치하지 않는다.

## 3. 맵 별칭

`GET /api/where-am-i/v3/map-aliases`는 공개 조회이며 본문·email이 없다.

```json
{"status":200,"msg":"OK","data":{"version":"sha256:...","aliases":[{"alias":"bigmap","map":"customs"},{"alias":"woods","map":"woods"}]}}
```

- 활성 행만 전체 스냅샷으로 반환한다. 목록은 1~1024개, 별칭 정규화 후 1~128자의 영문 소문자·숫자·공백·밑줄·하이픈만 허용한다.
- 클라이언트와 동일하게 trim → 소문자 → `_preset` 제거 후 중복 검사한다. DB의 정규화 unique 인덱스로도 충돌을 막는다.
- DB map_slug에는 고정 목록 CHECK를 두지 않는다. 신규 slug도 저장할 수 있다. 다만 현재 준비된 클라이언트가 알 수 없는 slug를 포함한 목록 전체를 거부하므로 API는 계약의 12개 slug 검증을 유지한다. 알 수 없는 slug가 활성화돼 있으면 HTTP 503으로 처리하며, 비활성 행은 목록에 포함하지 않는다. 새 slug를 공개하려면 클라이언트와 API 지원 목록을 함께 확장한다.
- version은 정렬된 공개 목록의 SHA-256이며 최대 128자 이내다. 활성 목록 내용이 바뀌면 version도 바뀌고, 동일한 공개 내용이면 같은 version이다. 숫자 크기로 비교하지 않는다.
- 최대 크기에서 별칭과 slug가 ASCII로 제한되므로 전체 응답은 256KiB 이하이다.
- 활성 목록이 없으면 404 MAP_ALIASES_NOT_FOUND. 목록 한도 초과·잘못된 데이터·DB 실패는 503 DESKTOP_METADATA_UNAVAILABLE이다. 클라이언트는 기존 캐시·내장값을 유지한다.
- 마이그레이션은 계약으로 확인된 bigmap→customs, woods→woods만 초기 등록한다. 기존 행·운영자 변경은 덮어쓰지 않는다. 나머지 내장 별칭은 클라이언트 fallback이 유지된다.

별칭의 map_slug는 **데스크톱이 지원하는 slug 사전**이다. platform_db.sql의 maps는 id가 PK이고 normalized_name은 nullable·비유일이므로 slug를 FK로 연결하지 않았다. 테이블 관계를 임의로 추측하거나 게임 지도 행을 자동 생성하지 않는다. 게임 지도 리소스를 조회하는 API는 기존 관계를 그대로 사용한다.

## 4. 신규 테이블과 배포

| 테이블 | 용도 |
|---|---|
| where_am_i_releases | 공개 버전·최소 지원 버전·공식 다운로드 메타데이터 |
| where_am_i_map_aliases | 활성 별칭과 클라이언트 slug 매핑 |

테이블·인덱스·제약조건 이름에는 버전 접미사를 붙이지 않았다. Python 모델·함수·DB 접근은 V3 규칙을 따른다. 기존 테이블과 legacy 구현은 삭제하지 않는다.

적용 SQL: `sql/migrations/20261019_where_am_i_desktop_metadata.sql`. 같은 정의를 platform_db.sql에 반영했다. 마이그레이션을 이미 적용했더라도 다시 실행하면 예전 ck_where_am_i_alias_map CHECK를 제거하며 기존 행은 유지한다. 기존 정보를 변경하지 않는 추가용 SQL이며 재실행 가능하다. 신규 환경 변수와 타이머 DB 테이블은 없다.

배포 순서:

1. V3 DB에 마이그레이션 적용.
2. 실제 공개할 릴리스 버전·최소 버전·다운로드 URL을 확인해 where_am_i_releases에 등록. is_active 기본값은 false이므로 검증 후 활성화한다. 현재 클라이언트의 기본 어셈블리 번호가 1.0.0.0이라는 사실만으로 배포 버전을 자동 등록하지 않는다.
3. 백엔드 배포 후 새 필드 전달·60초 이후 복원·공개 버전·별칭 조회 확인.
4. 클라이언트 배포 및 Windows에서 실제 응답·공식 다운로드 열기 확인.
5. 웹에서 Woods 자동 타이머를 연동하고 실제 게임 시간과 비교.

메타데이터 등록은 이번 범위에서 관리자 API를 만들지 않고 DB 운영 절차를 사용한다. SQL 예시로 등록할 때도 실제 확정한 값만 사용한다. 기존 공통 HTTP 제한을 적용하며 endpoint 전용 인증·별도 제한을 추가하지 않는다.

## 5. 경로 수집 문서 정책 갱신

경로 수집 API·테이블·중복 허용 정책은 그대로다. 클라이언트 최신 정책인 기존 저장 경로 최초 수집, 종류별 경로 해시로 성공 기록, 실패 항목 다음 실행 재시도를 기존 문서에 반영했다. 이메일·collection_source·새 endpoint는 추가하지 않는다. 서버 설정 조회·복원 기능이 아니다.

## 6. 외부 GraphQL 제한시간 조회 제거

`GET /api/live-map/v3/raid-duration/{normalized_name}`는 더 이상 tarkov.dev GraphQL에 요청하지 않는다. 기존 `{status,msg,data}` 및 data의 `{normalized_name,minutes}` 형식은 유지한다.

내부 `maps`에서 기존 BTR 조회와 같은 우선순위로 지도를 선택하고, 해당 지도의 활성 `live_map_btr_routes.raid_duration_seconds`가 모두 양수이며 한 값으로 일치할 때만 분 단위 기준값을 제공한다. 운행표가 없거나 기준이 다르거나 DB 조회가 실패하면 기존 실패 envelope인 `{status:200,msg:"FAIL",data:null}`을 반환한다. 비활성 운행표는 제외하며 기본 시간을 추측하거나 외부 조회로 보충하지 않는다. DB 변경은 다음 조회에 반영한다.

이 값은 BTR 운행표의 내부 기본 기준이며 실제 플레이 중인 레이드의 종료 시각을 보장하지 않는다. 새 exe의 자동 타이머는 계속 개인 이벤트의 raid_ends_at을 사용하고, 타이머가 없으면 수동 입력을 유지한다. 모든 지도에 임의의 35분 기준을 넣지 않는다. 이번 제거에는 추가 DB 마이그레이션이 필요 없다.

## 7. 분석 이력

레이드 상태·버전 확인·선택한 데스크톱 API 실패를 응답 전송 후 별도 트랜잭션에 기록한다. 요청·응답 계약과 클라이언트 필수 필드는 바꾸지 않는다. 적용 SQL은 `sql/migrations/20261019_where_am_i_analytics.sql`이며, 수집 범위·장애 시 유실·집계 쿼리는 [분석 이력 문서](where_am_i_analytics_v3.ko.md)를 따른다.

## 8. 수신 맵 별칭 변환

레이드 상태 수신에서 정식 slug는 그대로 사용하고, 그 밖의 원본 map은 활성 where_am_i_map_aliases로 변환한다. 원문은 requested_map, 확인된 slug는 map_slug에 기록하며 웹소켓 map은 확인된 slug 또는 null이다. 타이머가 있는 미매핑 요청은 422 RAID_MAP_UNRESOLVED이며 실패 이력에 원문을 보관한다. 타이머 없는 미매핑 상태는 정상 수집·전달하되 map은 null이다. 상세 정책과 기본 별칭 등록 SQL은 [분석 이력 문서](where_am_i_analytics_v3.ko.md)의 백엔드 별칭 매핑 절을 참고한다. 요청 필드명은 기존 map이며 requested_map을 프로그램에서 추가할 필요는 없다.
