# Review — quoted site id under a quoted key (round 1 of 1)

- **Reviewer:** `pls-x-reviewer`, claude-opus-5-5, effort high; working tree against `f2e378c`.
- **Verdict:** accept with fixes. No Critical, High or Medium. All five acceptance criteria met on the reviewer's own evidence (suites 3.12 384 OK, 3.10 384 OK skipped=2, node 15; the new tests fail with the parent's `ID_CONTEXT`, checked in memory).
- **git status before/after the call:** the reviewer changed nothing. Files that changed during the review were the Orchestrator's parallel eval work (case 001 run 3), committed separately in `5eff173`.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | Low | `HANDOFF.md` still said options A/B/C open, Nam to decide | Fixed: progress entry names option A, the fix, this review and TD-23; suite count 384 |
| F2 | Low | Escaped JSON inside a JS string (`{\"siteId\": \"797\"}`) and a backtick key still missed; mixed quotes work but untested | Mixed quotes added to the pure test (`y = {"siteId": '103'}`); the two rarer forms recorded as TD-23 (deadline: before the first takeover of a customer app) |
| F3 | Low | Over-matches of the old rule (`"siteId": "797-1"`, `"SITE_ID_COUNT": "797"`, `log("bad siteId", "797")`) now also apply to quoted values | No change: the same rule applied to one more form, not a new kind of over-match; pack restores each environment's number; `pls refs --keep` can protect a context |
| F4 | Low | Existing projects see a one-time diff on the next unpack (`"<n>"` → `${site:x}`), and L-REF-01 on such literals | Stated in the commit message and `HANDOFF.md` |

**Not verified by the reviewer, done by the Orchestrator:** `pls lint` on a fresh `git archive` copy of `pls-demo-inquiry` HEAD (`../_agent-scratch/demo-inquiry-lint-copy2/`): 37 issues, none L-REF (38 with one L-REF-03 before the fix). End to end on a real Pleasanter export: not verified (needs a person on dev).
