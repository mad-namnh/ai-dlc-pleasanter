# Review — P3-2 no app names in core

- **Reviewer:** `pls-x-reviewer`, model `sonnet`, effort `medium`; round 1 of 2; working tree against `a19fe9a`.
- **Verdict:** accept — 0 Critical, 0 High, 0 Medium, 3 Low. Reviewer ran: Python 448 OK, node 15 pass, criterion-1 grep 0 hits.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L1 | Low | Untracked `plans/2026-11-12-p3-3-…/` is not part of P3-2 | Not staged in the P3-2 commit |
| L2 | Low | Whole-name branch matched `login(`, `logo(`, `logic(` → "log or message text" | Fixed: whole names are case-sensitive `log` / `warn` / `error` / `notify` with an optional camel-case or `_` tail (`logEvent(`); negatives `login(`, `logo(` added to the test |
| L3 | Low | App name still in `docs/adr/0013`, `docs/plan.md`, `docs/review-criteria.md` G5 | No change: history and evidence documents, outside the core (A5 scope: `tools/`, `skills/`, `templates/`) |
