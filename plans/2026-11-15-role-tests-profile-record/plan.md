# Plan — Role tests as a recorded profile field

- **Tier:** Critical (profile records = guard inputs, ADR-0020; I4).
- **Source:** trial `pls-trial-store-promo` `design/decisions/2026-11-14-role-tests-deferred.md`: "`pls profile set` has no 'Role tests' key … so the row in CLAUDE.md was edited by hand".
- **Decision:** Nam 2026-11-15 — "Thành field có record".
- **Change:** `pls profile set "Role tests" deferred|per-role keys --approver --quote`; L-PRF-01 reports an unrecorded / hand-edited row; effective profile shows the recorded value; `pls init --approver` records it (quote includes `--stage`). Docs: architecture tables. Stop points: ADR-0020/0014 text (`proposed-adr-text.md`, Nam approves), template hard rule (`proposed-template-CLAUDE.md.patch`, Nam applies).
- **Acceptance:** (1) set with words → row + record; (2) hand edit reported, recorded value effective; (3) invalid value refused; (4) init records it; (5) new tests fail on the parent; (6) suites green incl. 3.10; (7) review no open Critical/High; (8) ADR text approved before commit; template patch reported as open until Nam applies it.
