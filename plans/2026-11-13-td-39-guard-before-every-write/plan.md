# Plan — TD-39: the write guard is read again before every site of bootstrap and every migration

- **Date / branch:** 2026-11-13 / `brownfield-adr`; parent `2930a42`
- **Tier:** Critical (write guard). Review `pls-x-reviewer`, `opus`, high.
- **Nam:** "lam tiep TD-39 va cac task con lai" (2026-11-13).
- **Change:** `write_guard_now(r, env, release, what)` (role, `allow_write`, outside dev the G4 record) is called before each `createsite` of `bootstrap` (through a `guard` of `H.bootstrap`; a refusal stops with status `stopped`, sites already created are bound) and before each migration folder of `migrate` (a refusal stops before the next `bulkupsert`; finished migrations stay recorded). The browser runner keeps one check per command (a person's fallback on dev, ADR-0014 TB-7) — stays in TD-39.
- **Acceptance:** 1. `allow_write` turned off (or the role changed, or the G4 record gone on stg) after the first site / migration → the next one is not sent, what was done is recorded, exit ≠ 0; 2. normal runs unchanged; 3. tests fail on the parent; suites green (3.10); 4. docs: tech-debt TD-39, architecture (bootstrap / migrate rows), ADR-0014 C1 note if any.
