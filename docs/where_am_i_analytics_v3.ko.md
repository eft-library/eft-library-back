# 데스크톱 분석 이력

## 수집 범위

기존 send-location의 user_location_request는 유지한다. 추가 테이블과 인덱스 이름에는 버전 접미사를 붙이지 않는다.

| 테이블 | 기록 |
|---|---|
| where_am_i_raid_state_events | 모델 검증을 통과한 send-raid-state 요청의 상태, 사용자 해시, 세션·시각·맵, 처리 결과, 성공 시 event_id |
| where_am_i_version_checks | 모델 검증을 통과한 check-version 요청의 현재 버전, 조회 결과 버전·업데이트 플래그, 처리 결과 |
| where_am_i_api_failures | 선택한 API의 검증·처리 실패 상태, 코드, 오류 필드명 |

실패 수집 대상은 send-raid-state, send-log-location, check-version, map-aliases, path-reports다. 경로 수집 성공은 기존 where_am_i_path_reports에 이미 저장되므로 중복 저장하지 않는다. 맵 별칭의 정상 조회는 별도 기록하지 않는다.

정상 요청의 모델·응답 형식과 exe 요청 필드는 바뀌지 않는다. 클라이언트·프론트 수정은 필요 없다. 레이드 처리에는 기존 WebSocket 발행 event_id를 분석 문맥으로 전달하는 내부 변경만 추가했다.

## 상태와 재시도

- HTTP 상태와 is_success를 구분한다. 2xx + msg=OK + 유효한 data가 있을 때 성공으로 기록한다. 기존 API의 HTTP 200 + msg=FAIL도 실패 이력에 들어간다.
- 실패한 정상 구조의 레이드 요청(404·409·503 등)도 상태 이력에 기록한다. WebSocket 발행에 성공하지 않았다면 event_id는 null이다.
- 버전 조회의 대상 없음(404), 메타데이터 오류(503)도 버전 확인 이력과 API 실패 이력에 기록한다. 조회 결과가 없으면 latest_version과 업데이트 플래그는 null이며 false로 성공을 가장하지 않는다.
- 422는 잘못된 상태를 정상 이력에 섞지 않도록 API 실패 테이블에만 기록한다. REQUEST_VALIDATION_ERROR와 body.session_id 등 필드명만 저장하고 원본 JSON·상세 오류 본문을 저장하지 않는다. 단, 레이드 요청의 map 문자열은 신규 맵·별칭 분석을 위해 requested_map에 별도로 보관한다. 알 수 없는 추가 필드명은 `<extra>`로 치환한다.
- 재시도는 모두 별도 행으로 남긴다. 같은 정상화 레이드 상태는 같은 user_key·state_hash로 묶을 수 있다. 요청이 다시 발행되면 event_id는 새 값일 수 있다. 고유 사용자 수·레이드 수를 단순 행 수로 계산하지 않는다.
- received_at은 서버 요청 처리 시작 시각, created_at은 분석 저장 트랜잭션 시각이다. elapsed_ms는 분석 저장 이전의 API 처리 소요 시간이며, 실제 지도 렌더링 시간이나 게임 촬영 시각이 아니다.

## 사용자·버전 정보

레이드 user_key는 기존 이메일 정리 후 값의 SHA-256이다. 이메일 원문과 IP는 새 테이블에 저장하지 않는다. 안정적인 사용자 구분을 위한 **가명 식별값**이며 익명화가 보장되는 것은 아니다. 계정 삭제 시 자동 FK cascade는 없고 보관 정책과 함께 별도 정해야 한다.

버전 확인은 사용자 정보가 없는 공개 API이므로 이메일·user_key를 추가하지 않는다. 집계는 요청 비율이며 설치 사용자 수·활성 사용자 수·업데이트 완료율이 아니다. API 실패의 app_version은 check-version의 current_version이나 path-reports의 app_version처럼 요청에서 알 수 있는 경우만 기록한다. 레이드 요청에 없는 앱 버전을 추측하거나 클라이언트 계약에 새 필수 필드를 추가하지 않는다.

경로 문자열·이메일 원문·로그인 토큰·다운로드 URL·원본 요청 본문·SQL 예외 매개변수는 이 분석 테이블에 넣지 않는다. 경로 수집 본 테이블은 기존 규격대로 클라이언트가 마스킹한 경로를 저장한다.

## 전달 로그 연결

레이드 성공 건의 event_id로 기존 서버 `location_published`, `location_forwarded` 로그와 연결한다. is_success=true는 상태 저장·Redis 발행 성공을 의미하고, 브라우저 수신·지도 표시 완료를 보장하지 않는다. 거부된 요청의 event_id는 null이다.

## 저장 장애와 한계

분석 저장은 HTTP 응답 본문 전송 후 BackgroundTask의 별도 V3Database 트랜잭션에서 수행한다. 기존 상태 저장·Redis 발행 트랜잭션과 공유하지 않는다. 분석 저장 예외는 종류만 로그에 남기고, 기존 응답과 전송 결과를 실패로 바꾸지 않는다. PostgreSQL 분석 트랜잭션에는 statement_timeout=1000ms, lock_timeout=250ms를 적용한다. 연결 수립·커넥션 풀 대기는 이 SQL timeout의 대상이 아니며 추가 DB 부하는 발생한다.

이력은 best-effort다. 프로세스 종료·DB 장애·분석 테이블 미적용 시 유실될 수 있으며 자동 재전송·영구 큐는 없다. 수집 누락을 숨기지 않도록 `Desktop analytics skipped` 로그를 남긴다. 공통 미들웨어에서 먼저 차단된 요청(예: 공통 IP 제한의 429), 존재하지 않는 경로의 404·405, 라우트 외부의 예기치 않은 500은 이 테이블에서 보장하지 않으며 기존 access/error 로그를 함께 확인한다.

보관 기간은 미확정이므로 이번에 자동 삭제 작업을 추가하지 않았다. 운영 기간과 규모를 보고 별도 보관·삭제 정책을 결정한다. 공개 조회 API나 관리자 조회 API는 추가하지 않는다.

## 배포

1. V3 DB에 `sql/migrations/20261019_where_am_i_analytics.sql` 적용.
2. 백엔드 배포. 신규 환경 변수와 클라이언트 변경은 없음.
3. 정상 레이드·버전 확인 요청 후 각 이력과 실패 응답 한 건을 확인.

SQL은 추가용이며 재실행 가능하다. platform_db.sql에도 같은 정의를 반영했다. 미적용 상태에서도 분석 저장 실패를 기존 기능 오류로 전파하지는 않지만, 반복 경고와 수집 누락을 막기 위해 SQL부터 적용한다.

## 분석 예시

일별 버전 확인 **요청** 분포:

```sql
SELECT date_trunc('day', received_at AT TIME ZONE 'Asia/Seoul') AS day_kst,
       current_version, count(*) AS requests,
       count(*) FILTER (WHERE update_available) AS update_available_requests
FROM where_am_i_version_checks
WHERE is_success
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

확인된 활성 세션의 맵별 타이머 확보 여부(세션 없는 구버전은 제외):

```sql
WITH sessions AS (
    SELECT user_key, session_id, map_slug,
           bool_or(timer_observed_at IS NOT NULL AND raid_ends_at IS NOT NULL) AS has_timer
    FROM where_am_i_raid_state_events
    WHERE is_success AND is_active AND session_id IS NOT NULL AND map_slug IS NOT NULL
    GROUP BY user_key, session_id, map_slug
)
SELECT map_slug, count(*) AS observed_sessions,
       count(*) FILTER (WHERE has_timer) AS sessions_with_timer
FROM sessions
GROUP BY map_slug;
```

최근 실패 분포:

```sql
SELECT endpoint, http_status, result_code, count(*)
FROM where_am_i_api_failures
WHERE received_at >= now() - interval '24 hours'
GROUP BY endpoint, http_status, result_code
ORDER BY count(*) DESC;
```

같은 상태 재전송 확인:

```sql
SELECT user_key, session_id, state_hash, count(*) AS attempts,
       min(received_at) AS first_received, max(received_at) AS last_received
FROM where_am_i_raid_state_events
GROUP BY user_key, session_id, state_hash
HAVING count(*) > 1
ORDER BY attempts DESC;
```

## 수신 맵 원문

레이드 상태·API 실패 테이블에 requested_map을 추가했다. 요청 map의 대소문자·공백·접미사를 변환하지 않고 저장한다. 현재 map_slug도 검증을 통과한 모델의 map 값이며, DB 지도 목록에 매핑됐다는 보증은 아니다. requested_map은 앞으로 정규화가 추가되어도 원문을 구분하기 위한 필드다.

알 수 없는 맵의 타이머 요청이 422로 거부돼도 where_am_i_api_failures.requested_map에서 확인할 수 있다. 새 맵을 수집한다고 API 지원 검증을 해제하지는 않는다. 문자열이 아닌 값·4096자 초과·PostgreSQL text가 받을 수 없는 NUL 포함 문자열은 null로 기록하고, 잘못된 JSON에는 추출할 맵이 없으므로 null이다. 전체 요청 본문과 다른 잘못된 입력값은 저장하지 않는다.

기존 운영 DB에는 sql/migrations/20261019_where_am_i_requested_map.sql을 분석 테이블 마이그레이션 다음에 적용한다. 신규 생성용 platform_db.sql과 원래 분석 마이그레이션에도 필드를 반영했다. 기존 행은 null이며 역추적해서 채우지 않는다.

```sql
SELECT requested_map, http_status, result_code, count(*)
FROM where_am_i_api_failures
WHERE endpoint = 'send-raid-state' AND requested_map IS NOT NULL
GROUP BY requested_map, http_status, result_code
ORDER BY count(*) DESC;
```
