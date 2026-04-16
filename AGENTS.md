# Schema Migration Guidance

The PostgreSQL schema has been fully refactored through normalization.

* Legacy schema file: `DB.sql`
* Current schema file: `platform_db.sql`

---

## Source of truth

`platform_db.sql` is the authoritative schema definition.
`DB.sql` is legacy reference only.

When implementing or modifying FastAPI code, always follow `platform_db.sql`.
Do not treat `DB.sql` as the current database structure.

---

## Backend refactor rules

* Existing FastAPI logic based on the old schema must be rewritten to match `platform_db.sql`.
* Do not assume old table names, column names, JSON fields, or denormalized structures still exist.
* Always verify table relationships and field definitions in `platform_db.sql` before writing code.
* Prefer rewriting queries and service logic cleanly for the new normalized structure instead of patching legacy SQL.

---

## Versioning convention (V3)

* All new database access must use `V3Database`.
* Newly created models, functions, services, and queries must use the `V3` prefix or suffix.

### Examples

* `UserModel` → `UserModelV3`
* `get_user_list` → `get_user_list_v3`
* `QuestService` → `QuestServiceV3`
* `fetch_items` → `fetch_items_v3`

---

## Migration strategy (non-destructive)

* Do not modify or delete existing legacy code.
* Always create new V3-based implementations instead of updating existing ones.
* Keep legacy endpoints, services, and queries intact for backward compatibility.

### Examples

* `get_user_list` → keep as-is

* create `get_user_list_v3`

* `QuestService` → keep as-is

* create `QuestServiceV3`

* existing endpoint → keep

* create `/v3/...` endpoint

---

## Implementation rules for V3

* All new logic must be implemented separately using V3 structure.
* Do not overwrite legacy functions, models, or queries.
* Do not refactor legacy code in-place.
* If migration is needed, implement V3 first, then switch usage explicitly later.
* Do not mix legacy (`DB.sql`) logic with V3 logic in the same function.

---

## Development rules

* Always inspect `platform_db.sql` before writing any database-related code.
* Replace old queries with queries based on the normalized schema.
* Update joins, foreign key traversal, and aggregation logic according to the new relational structure.
* If schema mapping is unclear, do not guess — leave a TODO or request clarification.
* Prefer consistency with the new schema over backward compatibility with legacy query patterns.

---

## Affected areas

This migration impacts:

* database access logic
* SQLAlchemy models
* raw SQL queries
* service/repository layers
* Pydantic schemas
* response shaping
* joins and aggregation logic

---

## Legacy handling

Use `DB.sql` only to understand previous behavior or compare legacy structures.

If `DB.sql` and `platform_db.sql` conflict, always follow `platform_db.sql`.

If a legacy field does not exist in `platform_db.sql`, treat it as removed unless an explicit replacement is defined.

---

## Important rule for code generation

When generating or modifying code:

1. Always read `platform_db.sql` first
2. Identify the correct table structure and relationships
3. Rewrite logic based on the normalized schema
4. Do not reuse legacy SQL patterns blindly
5. Do not guess missing fields or relationships

---

## Summary

* `platform_db.sql` = current schema (source of truth)
* `DB.sql` = legacy reference only
* All new work = V3
* Never modify legacy code → always create new V3 code
* Do not mix V2 and V3 logic
* When unsure → do not guess
