# Log — mail settings out of git

- 2026-11-16 Implemented (pls_http LIVE_ONLY_KEYS / with_live_only; pls.py logical, L-DEP-01, rollback files, lint; top-level import pls_http as HTTP — H is a local name inside _main). Tests test_pls + test_http; parent check (worktree of 1f2d2e5, removed): both FAIL.
- Docs: ADR-0010 as-built (Nam's words quoted), architecture L-SEC-01, inventory, TD-59.
- Suites: 3.12 624 OK, 3.10 624 OK (skipped=2), Node 16/16. Review started (pls-x-reviewer, opus, high; subagent 1/6).
- Review round 1: reject (H1–H3). All findings fixed (review.md). Re-running suites; review round 2 next.
- Suites after fixes: 3.12 625 OK, 3.10 625 OK (skipped=2), Node 16/16. Review round 2 started (subagent 2/6).
- Review round 2: accept with fixes (review.md). F2–F7 handled; F1 → proposed-wording-for-nam.md. STOP before commit (stop points 1, 2): waiting for Nam. Work tree keeps this task's changes; next tasks touch other paths only.
- Suites after round-2 fixes: 3.12 628 OK, 3.10 628 OK (skipped=2), Node 16/16.
- 2026-11-16 Nam, verbatim "2 duyệt" (to: approve proposed-wording-for-nam.md as written, change it, or another form): approved as written. The texts in ADR-0010 and architecture.md are those of proposed-wording-for-nam.md; inventory rows 97–100 say approved. Commit.
