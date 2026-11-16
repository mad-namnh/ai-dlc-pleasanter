# Review — nothing-to-convert migration

## Round 1 (pls-x-reviewer, opus, high) — reject

- **F1 High:** 3.12 suite red — apply re-check `except MI.MigrateError` refusal (pls.py ~3108) has no test.
- **F2 High:** `pls package` (prod) carries a nothing-to-convert folder; neither migrate nor apply runs there, so the emptiness check never runs on prod. ADR text silent.
- **F3 High:** folder `site` not tied to the data-impacting site: records on `equipment`, folder names empty `loans` → migrate ok, apply wrote both sites (reviewer scenario).
- **F4 High:** `migrate --rollback` refuses the whole release when one folder is nothing-to-convert → other folders' data cannot be rolled back.
- **F5 Medium:** re-check runs before the typed confirmation, not just before the write; remaining window not documented (C9).
- **F6 Medium:** count = records the operator's key can see (KB D36); no permission check, no TotalCount cross-check.
- **F7 Low:** re-check follows today's migration.json (dev has no G4 digest); run entry does not record nothing_to_convert / records read.
- **F8 Low:** untested: transport errors in the migrate read and the apply re-check; folder without backup/ or dry-run.md. Dead end: a `migrating` entry tells the person to roll back, which is refused.
- **F9 Low:** architecture.md:99, P5 skill, package README, confirmation text; "backup shows 0 records" not checked.

## Round 2 (pls-x-reviewer, opus, high) — reject; R2-H1 open → stop point 8

- **R2-H1 High:** `MI.read_nothing_to_convert` reads with `utf-8` and returns None on error (fails open); `MI.load` / `rj` read `utf-8-sig`. A migration.json with a BOM (PowerShell 5 `Set-Content -Encoding UTF8`) is accepted as nothing-to-convert by the folder checks but skipped by every new guard: prod plan, `pls package` (zip built after G4), F3 site tie, F4 rollback skip (rollback rc 2, m1 not rolled back). Reproduced in the reviewer's scratch. Fix: read with `utf-8-sig` through the same loader; guards refuse an unreadable migration.json; BOM tests.
- **R2-L1:** rollback skip reads today's folder; apply reads the run entry → decide the skip from the forward run entry.
- **R2-L2:** `nothing_to_convert` flag written after the first `migrating` record → set it before the first write.
- **R2-L3:** architecture.md:277 still says every folder has a rollback and a keyed bulkupsert.
- **R2-L4:** F3 site tie checked only at plan time (dev has no G4 digest) — within TD-54; could re-run in migrate.
- Round-1 F1–F9 fixed for normal files; suites 3.12/3.10 609 OK, Node 15/15; ADR text matches v2 word for word.

## Round 3 (pls-x-reviewer, opus, high; allowed by Nam) — accept with fixes; no Critical/High/Medium

- R2-H1, R2-L1–L3 fixed and pinned by tests (reviewer's own mutation checks). No input read differently by different paths (BOM, UTF-16, invalid JSON, duplicate keys, non-bool flag, non-string site probed).
- **R3-L1:** TD-54 did not say the site tie is plan-time only → TD-54 reworded.
- **R3-L2:** non-string `site` → TypeError in `nothing_to_convert_problems` (fails closed) → named problem + test.
- **R3-L3:** plan.md rollback line stale → updated.
- **R3-L4 (disposition):** ntc(X) + load(X) in one release: apply refuses after data was sent — fails safe (no config written); ADR-0004 Consequences put loads in a release of their own.
- Pre-existing, outside the diff → TD-55 (`MI.pending` ignores rollback entries), TD-56 (browser runner does not enforce the migration order).
