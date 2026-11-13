# Log — P2-6 ADR governance

Counts: subagent calls (not eval cases) 1/6, review rounds 1/2, fix attempts 0/3.

- 2026-11-11 | main session `claude-opus-5-5`; tier Critical (ADRs, approver rules, write opt-in) — strongest tier, no switch needed.
- 2026-11-11 | before the task: pending eval results of P1 0.6 (fable) committed as `3255e97` (suites 444 OK, node 15 pass).
- 2026-11-11 | scope checked against the code: A2 items 1–7 still without an ADR (`grep` of `docs/adr/` finds them only in ADR-0012 notes and ADR-0014 rows); A4 item 2 (migration order) and item 3 (runner on stg) already aligned by P0-5 / P0-7; item 5 (run-log failure) closed by P2-5; items 1, 4, 6, 7 still open.
- 2026-11-11 | decided without asking: three new ADRs (0020 gate records, 0021 setup profile / keys / env overrides, 0022 distribution) rather than amending ADR-0008, because ADR-0008 is Proposed and an amendment would mix two decisions; each new ADR is Proposed with options and a recommendation. No existing ADR's Status or Decision changed (stop point 1): the list for Nam is `decisions-for-nam.md`.
- 2026-11-11 | a python one-liner to add ADR citations to docstrings was denied by the permission rules; done with the Edit tool instead.
- 2026-11-11 | part 1 suites: Python 444 OK (3.12), node 15 pass. Python under `tools/pls` changed only in docstrings / comments; 3.10 not re-run for part 1.
- 2026-11-11 | part 2 written: ADR index with "Built and relied upon" column, architecture I4 / I7 / §4 / §7.3 / §8 / §10, `decisions-for-nam.md`, `proposed-CLAUDE-md-write-rule.patch` (stop point 3, not applied), HANDOFF.
- 2026-11-11 | subagent call 1/6: `pls-x-reviewer`, `opus`, effort `high`, round 1/2 — accept with fixes, 3 Medium + 5 Low, all fixed (`review.md`); `git status` unchanged by the call.
- 2026-11-11 | suites after the fixes: Python 444 OK (3.12), 444 OK skipped=2 (3.10), node 15 pass. Nam: commit after the review.
- 2026-11-11 | untracked `plans/2026-11-11-kb-gap-procedure/` belongs to another session (waiting for P2-6); not touched, not committed.
- 2026-11-11 | committed locally: `7899987` (ADR-0020…0022), `c166dc5` (index, architecture, decisions for Nam, patch, review, HANDOFF). Open for Nam: `decisions-for-nam.md`, the CLAUDE.md patch.
- 2026-11-11 | REPORT SENT
