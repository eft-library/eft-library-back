# 시즌 플리마켓 가격 연동 규격

## 정책

- `pvp`, `pve` 가격은 `season_id = null`로 저장한다.
- `pvp-season` 가격은 외부 `/pvp-season/season` 응답의 `data.id`를
  `season_id`로 저장한다.
- 지난 시즌 행을 삭제하지 않는다. 시즌 변경 후에도 `season_id`를 선택해 조회할 수 있다.
- `price_seasons.is_current = true`인 행은 최대 하나다.
- 클라이언트가 시즌을 지정하지 않으면 현재 시즌을 조회한다.

## Airflow 적재 계약

Airflow는 `/pvp-season/season`과 `/pvp-season/items`를 모두 정상적으로 받은 뒤
하나의 DB 트랜잭션에서 다음 작업을 수행한다.

1. 기존 `price_seasons.is_current`를 `false`로 변경한다.
2. 시즌 메타데이터를 `price_seasons`에 upsert하고 해당 시즌만 `is_current = true`로 설정한다.
3. 해당 `season_id`의 `item_prices`와 `item_trader_prices` 현재 스냅샷을 교체한다.
4. `item_price_history`에 `(item_id, game_mode, season_id, price_time)` 기준으로 upsert한다.
5. 트랜잭션을 커밋한 후 정적 JSON을 생성한다.

외부 API 오류, 시즌 ID 누락 또는 아이템 응답 검증 실패 시 트랜잭션을 시작하지 않는다.
다른 시즌의 가격과 히스토리는 삭제하지 않는다.

시즌 행은 다음 값을 사용한다.

| DB 컬럼 | 외부 시즌 응답 |
| --- | --- |
| `id` | `data.id` |
| `name` | 번역된 `data.name` |
| `starts_at` | `data.start`를 `timestamptz`로 변환 |
| `ends_at` | `data.end`를 `timestamptz`로 변환 |
| `is_current` | 현재 수집 대상이면 `true` |
| `collected_at` | 시즌을 처음 정상 수집한 시각 |
| `update_time` | 메타데이터를 마지막으로 확인한 시각 |

가격 테이블에 추가된 `season_key`는 DB 생성 컬럼이므로 INSERT 또는 UPDATE 대상에
포함하지 않는다. `item_trader_prices.id`를 계속 생성한다면 시즌 행은
`{game_mode}:{season_id}:{item_id}:{trader_id}`처럼 시즌 ID까지 포함한다.

기존 DAG의 UPSERT 충돌 키는 마이그레이션 이후 사용할 수 없다. 다음 키로 변경한다.

| 테이블 | `ON CONFLICT` 키 |
| --- | --- |
| `item_prices` | `(item_id, game_mode, season_key)` |
| `item_trader_prices` | `(item_id, game_mode, season_key, trader_id)` |
| `item_price_history` | `(item_id, game_mode, season_key, price_time)` |

세 테이블의 INSERT 컬럼에는 `season_id`를 추가한다. PVP/PVE에는 `null`, 시즌에는
외부 시즌 ID를 전달한다.

## 백엔드 API

### 시즌 목록

`GET /price/v3/seasons`

현재 시즌과 보관된 지난 시즌을 시작일 내림차순으로 반환한다.

### 가격 검색

`GET /price/v3/search?page=1&page_size=20&word=M4A1&season_id={season_id}`

- `season_id` 생략: 현재 시즌
- `season_id` 지정: 해당 시즌
- 기존 `pvp`, `pve` 결과에는 영향을 주지 않는다.
- 응답의 `prices`, `history_by_type`, `trader_prices`에 `pvp-season` 키가 항상 존재한다.

### 가격 랭킹

`POST /price/v3/top`

```json
{
  "categoryList": ["Ammo"],
  "seasonId": "external-season-id"
}
```

`seasonId`를 생략하면 현재 시즌을 사용한다. 응답에는 기존 목록과 함께
`pvp-season_top_list`, `selected_season_id`가 포함된다.

## 기존 DB 반영

운영 반영 전 `sql/migrations/20261007_price_seasons.sql`을 실행한다. 마이그레이션은
기존 PVP/PVE 행에 `season_id = null`을 유지한다. 출처 시즌을 알 수 없는 기존
`pvp-season` 행은 삭제하지 않고 `legacy-unidentified` 시즌으로 이동한다.

이 마이그레이션은 가격 테이블의 기본키를 변경하므로 기존 Airflow DAG와 호환되지
않는다. 다음 순서로 같은 배포 작업에서 전환한다.

1. 기존 가격 수집 DAG를 일시 중지한다.
2. DB 마이그레이션을 적용한다.
3. 새 UPSERT 키를 사용하는 Airflow DAG와 이 백엔드를 배포한다.
4. 시즌·PVP·PVE 시험 적재와 API 조회를 확인한다.
5. 가격 수집 DAG를 다시 시작하고 정적 JSON을 재생성한다.
