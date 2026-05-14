# DB 스키마를 갈아엎었더니 마이그레이션이 일이 되었다

이번에 타르코프 도서관 백엔드의 DB 구조를 정리하면서 기존 데이터를 새 스키마로 옮기는 작업을 진행했습니다.

기존 DB는 오래 운영하면서 기능이 하나씩 붙은 형태였습니다.
처음에는 빠르게 만들기 좋았지만, 시간이 지나면서 테이블 이름, JSON 필드, 다국어 데이터, 유저 데이터가 한 구조 안에 섞이기 시작했습니다.

결국 새 기능을 붙일 때마다 이런 고민이 생겼습니다.

```text
이 필드는 어디에서 온 값이지?
이 JSON 안에 어떤 구조가 들어있지?
영어/한국어/일본어 데이터는 어떻게 분리해야 하지?
기존 API를 건드리면 운영 중인 기능이 깨지지 않을까?
```

그래서 기존 `DB.sql` 기반 구조를 유지한 채, 새로 정규화된 `platform_db.sql`을 만들고 V3 스키마로 분리하는 방향을 선택했습니다.

## 마이그레이션 원칙

이번 작업에서 가장 중요하게 잡은 원칙은 비파괴 마이그레이션이었습니다.

기존 코드를 수정하거나 삭제하지 않고, 새 구조를 따르는 V3 구현을 따로 만들었습니다.

```text
기존 DB       -> DataBaseConnector
새 V3 DB      -> V3Database
기존 스키마    -> DB.sql
새 스키마      -> platform_db.sql
```

즉, 기존 서비스는 그대로 두고 새 DB에 데이터를 복사했습니다.

이렇게 한 이유는 단순합니다.
운영 중인 서비스에서 DB 구조를 한 번에 바꾸는 것은 위험하기 때문입니다.

새 스키마로 데이터를 먼저 옮기고, API나 서비스 로직은 이후 명시적으로 V3 쪽으로 전환할 수 있게 만들었습니다.

## 마이그레이션 스크립트 구조

마이그레이션 스크립트는 크게 세 단계로 나누었습니다.

```text
1. 기존 DB에서 select
2. V3 스키마에 맞는 payload로 변환
3. V3 DB에 upsert
```

예를 들어 기존 `extraction_i18n`, `transit_i18n` 데이터는 새 스키마에서는 `map_points` 테이블로 합쳐졌습니다.

기존에는 탈출구와 환승 지점이 별도 테이블이었지만, 새 구조에서는 둘 다 맵 위의 포인트라는 공통 개념으로 볼 수 있었기 때문입니다.

```python
payloads = [
    *[build_map_point_payload(dict(row), "extraction") for row in extraction_rows],
    *[build_map_point_payload(dict(row), "transit") for row in transit_rows],
]
```

이런 식으로 기존 테이블의 의미를 새 스키마의 도메인 기준으로 다시 매핑했습니다.

## 다국어 JSON 분리

기존 데이터에는 `name`, `description`, `guide` 같은 필드가 JSON 형태로 들어있는 경우가 많았습니다.

예를 들면 이런 형태입니다.

```json
{
  "en": "Factory",
  "ko": "팩토리",
  "ja": "ファクトリー"
}
```

V3 스키마에서는 이를 명시적인 컬럼으로 분리했습니다.

```text
name_en
name_ko
name_ja
```

그래서 공통 함수로 언어별 값을 꺼내도록 했습니다.

```python
def get_lang_value(value, lang):
    if value is None:
        return None

    if isinstance(value, dict):
        return value.get(lang)

    return str(value)
```

이렇게 해두니 `story`, `information`, `main_contents`, `menu_groups`처럼 다국어 필드를 가진 테이블에서 같은 방식으로 변환할 수 있었습니다.

## upsert를 사용한 이유

마이그레이션 중에는 같은 데이터를 여러 번 실행할 수 있어야 했습니다.

한 번에 모든 테이블을 완벽하게 옮기기보다, 테이블 단위로 실행하고 확인하면서 보정하는 방식이 더 안전했습니다.

그래서 insert만 사용하지 않고 `on conflict do update`를 사용했습니다.

```sql
on conflict (id) do update set
    name_en = excluded.name_en,
    name_ko = excluded.name_ko,
    name_ja = excluded.name_ja,
    update_time = excluded.update_time;
```

이렇게 하면 같은 마이그레이션을 다시 실행해도 중복 데이터가 쌓이지 않고 최신 값으로 갱신됩니다.

## 까다로웠던 부분

가장 신경 쓴 부분은 JSON 안에 들어있던 데이터를 새 관계형 구조로 풀어내는 일이었습니다.

특히 퀘스트 목표 데이터는 기존에는 `quest_i18n.objectives` 안에 배열로 들어있었습니다.

새 구조에서는 `quest_objectives` 테이블로 분리했습니다.

```text
quest_i18n.objectives
-> quest_objectives
```

그래서 각 퀘스트의 objectives 배열을 순회하면서 objective 단위 payload를 만들었습니다.

```python
for sort_order, objective in enumerate(objectives, start=1):
    payload = build_quest_objective_payload(quest_id, objective, sort_order)
```

기존에는 하나의 JSON 필드였지만, 새 구조에서는 검색, 조인, 정렬이 가능한 데이터가 되었습니다.

## 커뮤니티 댓글과 ltree

커뮤니티 댓글도 특이한 부분이 있었습니다.

댓글은 계층 구조를 가지고 있기 때문에 V3 스키마에서는 PostgreSQL의 `ltree`를 사용했습니다.

```sql
path LTREE
```

마이그레이션할 때는 기존 path 값을 문자열로 가져온 뒤 insert 시점에 `ltree`로 캐스팅했습니다.

```sql
cast(:path as ltree)
```

댓글처럼 부모-자식 관계가 있는 데이터는 단순히 컬럼만 옮기는 것이 아니라, 이후 조회 방식까지 고려해서 옮겨야 했습니다.

## 정리

이번 마이그레이션은 단순히 테이블 이름만 바꾸는 작업이 아니었습니다.

기존 서비스에서 자연스럽게 쌓인 데이터 구조를 다시 도메인 기준으로 해석하고, 새 스키마에 맞게 재배치하는 작업에 가까웠습니다.

이번에 느낀 점은 다음과 같습니다.

```text
1. 마이그레이션은 insert 작업이 아니라 해석 작업이다.
2. 새 스키마가 기준이면 기존 구조에 끌려가면 안 된다.
3. 운영 중인 서비스에서는 비파괴 방식이 마음 편하다.
4. upsert 가능한 스크립트는 반복 검증에 유리하다.
5. JSON으로 빠르게 만든 데이터는 언젠가 관계형 구조로 풀어야 할 수 있다.
```

처음에는 단순히 "기존 DB에서 새 DB로 옮기면 되겠지"라고 생각했는데, 막상 해보니 데이터가 어떤 의미를 가지고 있는지 다시 확인하는 시간이 훨씬 길었습니다.

그래도 이번 작업 덕분에 이후 V3 API를 만들 때는 훨씬 명확한 기준을 가지고 작업할 수 있게 되었습니다.

`platform_db.sql`을 기준으로 스키마를 고정하고, 새 코드는 모두 `V3Database`를 사용하도록 분리했기 때문에 앞으로는 기존 구조와 새 구조를 섞지 않고 점진적으로 이전할 수 있을 것 같습니다.
