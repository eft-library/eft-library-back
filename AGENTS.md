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

## Naming and compatibility

* Do not add `V3` or `v3` to code identifiers, filenames, table names, or index names.
* All new database access for `platform_db.sql` must use `Database` from `database.py`.
* `DataBaseConnector` is the legacy database connection; keep it separate from `Database`.
* Existing API URLs, including `/v3/...`, must remain unchanged unless explicitly requested.
* Preserve existing environment variable names, Redis keys, cookies, and stored format identifiers.
* Keep legacy behavior and implementations separate; do not overwrite them when names collide.
* Use descriptive names such as `PlatformUserUtil` to distinguish normalized-schema implementations.
* Historical migration filenames remain stable so applied migration references are preserved.

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
* New code uses descriptive names without version suffixes
* Keep legacy implementations separate
* Do not mix legacy and normalized-schema logic
* When unsure → do not guess
