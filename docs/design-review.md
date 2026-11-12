# Design Review — Todo App Architecture

## Review status

**Review type:** Critical architecture review (senior/principal architect perspective)  
**Scope:** `docs/architecture.md` against `docs/requirements.md` and the existing Python/SQLite repository structure.  
**Outcome:** Architecture is directionally sound for the local single-user MVP, but several operational and implementation details needed to be made explicit. The architecture document has been updated to address the gaps below.

## Summary

The layered design (presentation → service/domain → repository → SQLite) is a good fit for a small local application and the existing codebase. SQLite and the existing Python modules avoid unnecessary infrastructure. Main risks were not the overall architecture, but ambiguity in schema compatibility, SQLite's Unicode search semantics, stable database-file location, error classification/recovery, migrations, timestamp resolution, and how rapid writes are ordered.

No new product decisions were explicitly confirmed by the user in this review. The “requirements-confirmed” items below come from `requirements.md`; technical recommendations are recorded as proposed and should not be mistaken for product approval.

## Findings and disposition

### F-01 — Existing schema and requirements model are not reconciled

**Severity:** High  
**Finding:** Requirements describe `completed`, while the existing repository uses `status` values `pending`/`done` and additional fields. Leaving the choice as an open question risks duplicate sources of truth, accidental data loss, or incompatible repository APIs.  
**Recommendation:** For the MVP, retain the existing `tasks` table and map `pending`/`done` to the domain completion boolean. Preserve extra columns unless the product owner approves a migration. Keep only one persisted source of truth for completion. If a schema change is later approved, migrate IDs/timestamps/data and test rollback/upgrade behavior.  
**Disposition:** Added as a recommended compatibility decision in `architecture.md`; owner confirmation remains required before implementation.

### F-02 — SQLite built-in case-insensitive matching is not generally Unicode-aware

**Severity:** High  
**Finding:** The requirement says case-insensitive search, but SQLite's default `LIKE` case behavior is ASCII-oriented. It may fail expectations for non-ASCII titles. A leading-wildcard contains query also generally cannot use a normal B-tree index effectively.  
**Recommendation:** Define deterministic locale-independent Unicode case-insensitive semantics. For a few thousand records, use Python `casefold()` matching over the successfully loaded/relevant set and benchmark. If search is moved to SQLite or the data grows, select and test a Unicode-aware collation/FTS strategy. Do not claim a normal index solves `%query%` performance.  
**Disposition:** Architecture updated with the semantic requirement and implementation options.

### F-03 — Database path may vary with process working directory

**Severity:** High  
**Finding:** A relative default such as `todo.db` can create different databases depending on how the app is launched, making saved todos appear to disappear.  
**Recommendation:** Use a stable OS-appropriate application-data directory for the normal runtime; allow an explicit configuration override for development/tests. Handle directory creation and permission errors without replacing the database.  
**Disposition:** Added to database-manager responsibilities.

### F-04 — Failure handling did not classify operational SQLite errors or define recovery behavior

**Severity:** High  
**Finding:** Generic “storage error” handling is insufficient for locked database, read-only/permission, disk-full/I/O, migration failure, and corruption. Automatically recreating a corrupt/unreadable file could destroy recoverable user data.  
**Recommendation:** Map storage failures to typed internal categories, set a bounded SQLite busy timeout, avoid infinite retries, roll back failed transactions, preserve an unreadable database, and present safe actionable guidance. Document backup/restore; do not claim SQLite alone protects against hardware failure.  
**Disposition:** Added error categories, lock handling, and fail-closed recovery guidance to `architecture.md`.

### F-05 — Schema migration strategy was too vague for an existing database

**Severity:** High  
**Finding:** The repository already has a schema and may contain data. “Add migrations when needed” does not specify how the application knows the current schema or protects existing records.  
**Recommendation:** Version schema changes using `PRAGMA user_version` or an equivalent migration table. Run migrations transactionally where supported, preserve/backup data before risky migrations, and test upgrades from representative existing versions. Never silently replace the database.  
**Disposition:** Added versioning, migration, and test expectations.

### F-06 — Timestamp guarantee may fail for rapid updates

**Severity:** Medium  
**Finding:** A timestamp source with millisecond or second precision can assign the same `updated_at` to consecutive rapid changes, contradicting the requirement that it changes on every modification. Clock adjustments can also complicate ordering.  
**Recommendation:** Choose a single UTC representation with sufficient precision and ensure the new `updated_at` is strictly later than the previous value for that record when a successful change commits. Keep `created_at` immutable.  
**Disposition:** Added explicit timestamp behavior; exact representation remains an implementation detail to settle.

### F-07 — “Serialize mutations” needs an implementation boundary

**Severity:** Medium  
**Finding:** Saying to serialize writes does not specify how same-record rapid updates avoid stale state. SQLite serializes writers at the database level, but that alone does not ensure the application applies user-intended operation ordering or prevents stale full-record updates.  
**Recommendation:** Within the single process, serialize mutations at least per todo ID or use an ordered command queue. Prefer field-specific SQL updates, define order by service acceptance, and return committed rows. Keep multi-process conflict resolution out of MVP while handling locks safely.  
**Disposition:** Added to architecture reliability rules.

### F-08 — SQLite constraints and Python validation can disagree on whitespace

**Severity:** Medium  
**Finding:** A database check using SQLite's default `trim()` does not recognize all Unicode whitespace that Python `str.strip()` recognizes. Relying on the SQL constraint alone may permit a title rejected by the service, or vice versa.  
**Recommendation:** Make service normalization/validation authoritative and keep database checks as a second line of defense for length and boolean domain. Add tests for whitespace-only Unicode input and length boundaries.  
**Disposition:** Clarified in the suggested schema description.

### F-09 — Performance target needs a measurement plan and realistic search strategy

**Severity:** Medium  
**Finding:** The 1–2 second load target is given, but no benchmark data, representative dataset, or search measurement is specified. Loading all rows may be acceptable at a few thousand but is not an unlimited scalability strategy.  
**Recommendation:** Benchmark startup/list and live search with a few thousand representative records on the target runtime. Debounce live search if needed. Avoid premature caching, server infrastructure, or indexes that do not help substring search. Revisit pagination/FTS only if measurements or future scale require it.  
**Disposition:** Added benchmark guidance. Larger-scale pagination remains future scope.

## Requirements-confirmed decisions

These are commitments already present in `docs/requirements.md`:

- The MVP is local and single-user, with SQLite as persistence.
- Todos use stable IDs; operations do not target list positions.
- A todo has a title, completion state, `created_at`, and `updated_at` at minimum.
- Titles are trimmed, non-empty after trimming, and limited to 255 characters.
- Search is case-insensitive and combines with status filters using AND behavior.
- Search/filter do not mutate persisted data.
- Failed reads/writes must not crash the app or be represented as success; the last successfully persisted data remains authoritative.
- Loading a few thousand records should take approximately 1–2 seconds on a typical developer machine.
- Multi-user/cross-device sync, retry controls, offline queues, and undo are not MVP requirements.

## Recommended technical decisions — pending owner confirmation

1. Preserve the existing `tasks` table and its extra fields for MVP compatibility; map `pending`/`done` to the domain `completed` boolean. Keep one persisted completion representation.
2. Store the database in a stable application-data directory, with an explicit override for tests/development.
3. Use versioned migrations and preserve the original database on migration/corruption failures; never silently recreate over an unreadable database.
4. Define search as locale-independent Unicode case-insensitive matching. Start with Python `casefold()` for the expected small dataset and benchmark before selecting SQLite FTS/extension support.
5. Ensure `updated_at` strictly advances on every successful modification, in UTC, while `created_at` remains unchanged.
6. Serialize same-process mutations per todo ID (or equivalent ordered queue), use field-specific updates, and rely on bounded SQLite lock handling rather than unbounded retry.
7. On corruption or I/O failure, fail closed, preserve the database file, show a clear unavailable state, and provide recovery/backup guidance rather than showing an empty list.

## Open decisions / owner sign-off

- Confirm whether the existing schema mapping recommendation is acceptable, including preservation of description, priority, and due-date columns.
- Identify the actual presentation entry point/framework; architecture keeps it replaceable because the current requirements do not specify it.
- Select exact UTC timestamp representation and implementation for strictly advancing `updated_at`.
- Decide where user backups live and what recovery instructions the app should present.
- Confirm Unicode search semantics and whether Python-side filtering meets the performance target after measurement.

## Architecture document update instruction and completion

Copilot: update `docs/architecture.md` when this review identifies a material design gap. In particular, ensure it records the schema compatibility strategy, Unicode search limitations, stable database path, migration/error recovery, timestamp precision, mutation ordering, and performance validation.

**Update status:** The architecture document has been revised to include these recommendations and their pending-approval status. No unconfirmed recommendation is represented as an agreed product decision.
