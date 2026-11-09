# 총기 모딩 원천 데이터 스키마

설계 기준: `platform_db.sql` 및 Airflow 저장소 `tests/item.json` (2026-11-10 확인).
이번 범위는 테이블 설계와 생성 DDL이다. 수집 작업·조회 API·실제 장착 판정·성능 계산은 포함하지 않는다.

## 생성 DDL과 기존 테이블

- 최신 전체 정의: `platform_db.sql`
- 기존 DB에 추가 적용: `sql/migrations/20261110_weapon_modding.sql`
- 기존 `items`의 이름·이미지·무게·크기를 재사용한다.
- 기존 `weapon_items`의 총기 제원과 `weapon_allowed_ammo`의 호환 탄약 관계를 재사용한다.
- 기존 `items.category`, `parent_category`는 문자열 분류이므로 원천 카테고리 ID 관계의 대체물이 아니다. 변경하거나 덮어쓰지 않는다.
- 테이블·인덱스 이름에는 버전 접미사를 사용하지 않는다.

## 테이블 12개

| 테이블 | 역할 | PK / 유니크 |
| --- | --- | --- |
| `item_categories` | 원천 `itemCategories`의 ID·부모·이름 | `id` |
| `item_category_memberships` | 아이템 `categories[]` 전체 소속 | `(item_id, category_id)` |
| `item_slots` | 총기·파츠의 슬롯 | `(item_id, slot_id)`, `(item_id, sort_order)` 유니크 |
| `item_slot_item_filters` | 슬롯별 아이템 허용·제외 관계 | `(item_id, slot_id, filter_type, sort_order)` |
| `item_slot_category_filters` | 슬롯별 카테고리 허용·제외 관계 | `(item_id, slot_id, filter_type, sort_order)` |
| `item_conflicting_items` | 원천 방향의 아이템 충돌 | `(item_id, sort_order)` |
| `item_conflicting_slots` | 원천 슬롯 ID 충돌 | `(item_id, sort_order)` |
| `item_conflicting_categories` | 원천 카테고리 충돌 | `(item_id, sort_order)` |
| `item_mod_properties` | 파츠 성능·중첩 배율 | `item_id` |
| `item_presets` | 프리셋의 기본 아이템·기본 여부·완성 성능 | `preset_item_id` |
| `weapon_preset_links` | 총기의 프리셋 목록·기본 프리셋 참조 | `(weapon_item_id, preset_item_id)`, 기본 참조는 총기당 최대 1개 |
| `item_preset_components` | 프리셋 구성품·수량·속성 | `(preset_item_id, component_index)` |

관계 테이블의 PK는 같은 원천 관계 또는 같은 배열 위치가 반복 INSERT되는 것을 방지한다.
샘플의 allowedItems에는 중복 참조 1건, conflictingItems에는 30건이 있다. 필터와 충돌 배열은
원본 순번으로 식별하여 동일 대상 ID의 반복도 그대로 보존한다. ID 기반 역조회 인덱스는 별도로 유지한다.
허용과 제외는 별도 행으로 공존할 수 있다. 인덱스는 PK의 소유자→하위 관계 조회와
대상 아이템·카테고리·슬롯→소유자 역조회, 프리셋 정렬에 맞춰 구성했다.
JSONB는 원본 보존용이며 아직 내용 검색 요구가 없어 GIN 인덱스는 추가하지 않았다.

## 원천 매핑

### 카테고리와 슬롯

- `data.itemCategories[id]` → `item_categories`: `id`, `parent` → `parent_id`, `name` → `name_key`, `normalizedName` → `normalized_name`.
- 원천 최상위 `parent: ""`는 FK가 가능한 SQL NULL로 정규화한다. ID 자체를 변경하지 않는다.
- 이름 원본은 번역 키일 수 있다. `name_key`를 보존하고 언어별 번역은 `name_en/ko/ja`에 적재한다. 번역이 없으면 NULL이며 임의 번역을 만들지 않는다.
- `item.categories[]` → `item_category_memberships`. 원천이 상위 카테고리를 함께 제공하면 모두 그대로 저장한다. `handbookCategories`는 별도 분류이므로 혼합하지 않는다.
- `item.properties.slots[]` → `item_slots`: 소유 `item.id` → `item_id`, `id` → `slot_id`, `nameId` → `name_id`, `name` → `name_key`, `required` → `required`, 배열 인덱스 → `sort_order`.
- 원천 슬롯 코드의 철자(`mod_reciever` 등)도 수정하지 않는다. 슬롯 ID를 전역 PK로 가정하지 않는다.
- 모든 배열 순번은 0부터 시작한다. 조건 배열의 순번은 각 조건 종류 안에서의 순번이다.

| 원천 슬롯 필터 | 대상 테이블 | `filter_type` |
| --- | --- | --- |
| `filters.allowedItems[]` | `item_slot_item_filters.target_item_id` | `allowed` |
| `filters.excludedItems[]` | `item_slot_item_filters.target_item_id` | `excluded` |
| `filters.allowedCategories[]` | `item_slot_category_filters.category_id` | `allowed` |
| `filters.excludedCategories[]` | `item_slot_category_filters.category_id` | `excluded` |

### 충돌

`conflictingItems[]`, `conflictingSlotIds[]`, `conflictingCategories[]`는 각각 충돌 테이블로 저장한다.
원천 방향·ID·순서를 보존하며, 충돌을 임의로 대칭화하거나 역방향 행을 만들지 않는다.

**샘플에서 충돌 대상 슬롯 ID 9개가 슬롯 정의 목록에 없다.** 따라서 `item_conflicting_slots`의
소유 아이템 FK만 적용하고 대상 슬롯 ID에는 FK를 두지 않는다. 대상 소유 아이템을 추정하지 않는다.
후속 조회에서는 `item_slots.slot_id`로 LEFT JOIN하며 미해결 ID도 노출할 수 있다.
현재 샘플의 아이템·카테고리 참조는 모두 마스터에 존재하므로 해당 관계에는 FK를 둔다.

### 파츠 성능

| 원천 | `item_mod_properties` |
| --- | --- |
| `properties.propertiesType` | `properties_type` |
| `properties.ergonomics` | `ergonomics` |
| `properties.recoilModifier` | `recoil_modifier` |
| `properties.accuracyModifier` | `accuracy_modifier` |
| `properties.zoomLevels` | `zoom_levels` JSONB |
| 루트 `ergonomicsModifier` | `ergonomics_modifier` |
| 루트 `recoilModifier` | `item_recoil_modifier` |
| 루트 `accuracyModifier` | `item_accuracy_modifier` |

예: M4A1 상부 리시버는 nested recoilModifier가 `-0.01`, 루트 값이 `-1`이다.
서로 다른 필드를 덮어쓰거나 스케일을 변환하지 않고 각각 보존한다.
`zoomLevels: [[1, 4], [2.5]]`는 배열의 중첩·순서·수치를 유지한다.
NULL과 0, NULL과 빈 배열을 구분한다. 신규 성능 필드·계산식은 확정 후 추가한다.
총기의 기본 인체공학·반동은 기존 `weapon_items`를 사용하고 이 테이블에 중복 적재하지 않는다.
프리셋 완성 성능도 아래 `item_presets`를 사용한다.

### 프리셋

샘플의 `ItemPropertiesPreset`은 총기뿐 아니라 방어구도 포함한다. 마스터는 `item_presets`로
공통 표현하고 총기별 원천 참조는 `weapon_preset_links`로 구분한다.

- 프리셋도 기존 `items`에 먼저 적재한다. 프리셋 이름·이미지·무게를 별도 복제하지 않는다.
- 프리셋 `item.id` → `preset_item_id`, `properties.baseItem` → `base_item_id`.
- 프리셋 `properties.default` → `item_presets.is_default`. 미확인 값에 false를 기본 적용하지 않는다.
- 프리셋 `properties.ergonomics`, `recoilVertical`, `recoilHorizontal`, `moa` → 대응 numeric 컬럼.
  완성 상태 제원은 원천 값 그대로이며, 기본 총기 제원과 합산하지 않는다.
- 총기 `properties.presets[]`의 관계는 `is_listed=true`, 원본 배열 순번을 `sort_order`에 저장한다.
- 총기 `properties.defaultPreset`가 가리키는 관계는 `is_default_reference=true`이다.
  목록에도 있으면 두 플래그가 모두 true이며, 목록에 없다면 `is_listed=false`, `sort_order=NULL`로 저장한다.
- `item_presets.is_default`와 총기의 `is_default_reference`는 서로 다른 원천 필드이다.
  불일치를 임의로 고치거나 하나에서 다른 값을 추론하지 않는다.
- `containsItems[]`의 배열 인덱스 → `component_index`, `item` → `item_id`, `count` → `quantity`, `attributes` → JSONB 객체.
  동일 아이템이 반복되어도 합산하거나 중복 제거하지 않는다. `attributes`의 키·중첩·값을 보존한다.
- 구성품에 원천 부모·슬롯 정보가 없으므로 해당 컬럼 자체를 추가하지 않았다.
  이 목록으로 실제 장착 트리를 복원했다고 표시해서는 안 된다.

## 다단계 관계 조회 예시

M4A1 `5447a9cd4bdc2dbd208b4567`의 리시버 슬롯에서 상부 리시버
`55d355e64bdc2d962f8b4569`가 허용되고, 그 리시버의 `mod_sight_rear` 슬롯에
가늠자 `55d5f46a4bdc2d1b198b4567`가 허용되는 관계를 샘플에서 확인했다.

```sql
select gun.id as weapon_id, receiver.id as receiver_id,
       rear_slot.slot_id, sight.id as sight_id
from items gun
join item_slots receiver_slot on receiver_slot.item_id = gun.id
join item_slot_item_filters receiver_filter
  on receiver_filter.item_id = receiver_slot.item_id
 and receiver_filter.slot_id = receiver_slot.slot_id
 and receiver_filter.filter_type = 'allowed'
join items receiver on receiver.id = receiver_filter.target_item_id
join item_slots rear_slot on rear_slot.item_id = receiver.id
join item_slot_item_filters sight_filter
  on sight_filter.item_id = rear_slot.item_id
 and sight_filter.slot_id = rear_slot.slot_id
 and sight_filter.filter_type = 'allowed'
join items sight on sight.id = sight_filter.target_item_id
where gun.id = '5447a9cd4bdc2dbd208b4567'
  and receiver.id = '55d355e64bdc2d962f8b4569'
  and rear_slot.name_id = 'mod_sight_rear';
```

이 쿼리는 원천의 명시적 허용 경로를 보여주는 예시이며 최종 호환 판정이 아니다.
카테고리 허용·제외와 충돌 조건까지 평가하는 판정기는 후속 작업이다.
깊이가 가변적인 조회는 재귀 CTE로 확장할 수 있으며, 순환 관계에 대비한 방문 경로 검사가 필요하다.

## Airflow 반복 동기화 계약

1. 원천 스냅샷이 완전한지 검증한다. 누락 필드·부분 응답을 빈 배열로 간주해 관계를 삭제하지 않는다.
2. 트랜잭션 안에서 카테고리, 기존 아이템·총기 마스터를 먼저 UPSERT한다.
   카테고리 부모 FK는 커밋 시 검사하므로 같은 트랜잭션에서 부모·자식을 순서와 무관하게 적재할 수 있다.
3. 슬롯·파츠 성능·프리셋 마스터를 PK로 UPSERT하고, 필터·소속·충돌·프리셋 참조·구성품을 반영한다.
4. 필터·충돌의 배열 순번 PK는 위치 식별자이며 영구적인 관계 ID가 아니다. 순서가 바뀌면
   같은 위치의 대상 ID도 갱신해야 한다. 원본 중복 참조를 제거하지 않는다.
   관계 동기화는 INSERT만 반복하지 않는다. 소유자별 완전한 스냅샷 안에서 UPSERT 후 사라진 행을 삭제하거나,
   해당 소유자의 관계 행을 삭제·재삽입한다. 순서 변경 시 `item_slots`의 순번 유니크 충돌을 피하도록
   해당 소유자의 슬롯과 필터를 트랜잭션 안에서 재삽입한다.
5. 기본 프리셋 변경 시 기존 링크의 `is_default_reference`를 먼저 해제하고 새 링크를 설정한다.
   원천의 `is_listed`와 순번은 유지한다. 구성품은 순번이 바뀔 수 있어 프리셋별 목록 교체가 단순하다.
6. FK 대상이 누락되면 ID를 만들어 채우지 말고 마스터를 보완하거나 해당 스냅샷을 실패시킨다.
   충돌 슬롯의 미해결 ID 보존은 위에서 정의한 예외이다.
7. 마스터의 `collected_at`, `update_time`은 UPSERT 시 명시적으로 갱신한다. DEFAULT now()는 INSERT에만 적용된다.
8. 원천 삭제 시 참조 관계를 먼저 정리한다. 소유 마스터 삭제는 하위 관계에 CASCADE되지만,
   대상 아이템·카테고리·프리셋 삭제는 RESTRICT로 보호된다. 불완전 수집을 원천 삭제로 해석하지 않는다.

새 테이블은 게임 모드·시즌별 스냅샷을 분리하지 않는 기존 `items`와 같은 범위이다.
수집 시 authoritative 원천 모드 하나를 정하고 서로 다른 모드 데이터를 같은 키에 교대로 덮어쓰지 않는다.
모드별 차이가 필요하면 기존 아이템 체계와 함께 별도 설계한다.

## 적용과 검증

DDL은 운영 DB에 직접 실행하지 않았다. 기존 DB 적용은 아래 추가 마이그레이션만 사용한다.
전체 `platform_db.sql`을 재실행하는 방식으로 적용하지 않는다.

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/migrations/20261110_weapon_modding.sql
.venv/bin/python -m unittest tests.test_weapon_modding_schema -v
```

`CREATE TABLE/INDEX IF NOT EXISTS`로 같은 생성 DDL을 재실행할 수 있다.
이미 존재하지만 구조가 다른 테이블을 자동 교정하는 기능은 아니므로 기존 동명 테이블은 적용 전 확인한다.

### 검증 결과

- 격리 PostgreSQL에서 생성 DDL 재실행, 기존 행 보존, FK·유니크 제약, 슬롯 삭제 CASCADE,
  중복 필터·충돌·구성품 보존, 기본 프리셋 참조, 중첩 배율 및 다단계 조회 테스트 8개 통과.
- 원본 샘플 전체를 임시 DB에 넣어 FK와 제약조건을 검증하고 롤백했다.
  아이템 5,498개, 카테고리 112개, 슬롯 3,673개, 슬롯 아이템 필터 40,854개,
  아이템 충돌 행 14,160개, 프리셋 500개, 프리셋 구성품 4,695개를 처리했다.
- 카테고리 허용·제외 필터는 현재 샘플에 없어 테스트 데이터로 별도 검증했다.
- M4A1 → 상부 리시버 → 가늠자 슬롯의 명시적 허용 후보 16개를 조회했다.
- 정의가 없는 충돌 슬롯 ID 9개도 그대로 보존됐다.
