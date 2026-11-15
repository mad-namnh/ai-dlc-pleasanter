# Plan — classify `Formulas[]` and access lists (settings coverage WS2.1 + 2.2)

- **Tier:** Critical (ADR-0004 change classes).
- **Source:** `plans/2026-11-15-settings-coverage/` (inventory A, plan WS2). Order approved by Nam ("3.ok", 2026-11-15).
- **Change:** `classify`: `settings.Formulas…` → data-impacting (ADR-0004 Decision 1 already says "formula changed"; 1.5.2 records formulas in `Formulas[]`, so the old `Columns[x].Formula` rule never fired). `settings.StatusControls…` and `Groups/Users/Depts` of `Views` / `Exports` / `DashboardParts` (path, or a whole item naming them) → permission-impacting. No ADR Decision change (Decision 1 unchanged; permission rules are not in the Decision); ADR-0004 Consequences gets an as-built note.
- **Not in this task:** WS2.3 (multi-select storage — needs a probe), WS2.4 (release step for 同期 — after WS3c-2).
- **Acceptance:** (1) formula added / changed / removed → data-impacting with the source note; (2) the listed paths → permission-impacting; a view without access list stays config-only; (3) new tests fail on the parent; (4) suites green incl. 3.10; (5) review no open Critical/High.
