# Review — kb-verify extension (ADR-0026) and KB D36–D42

## Round 1 (pls-x-reviewer, opus, high, 2026-11-14) — verdict: reject

Scope: working tree against `d326a27` (excluding `.claude/settings.json`, `plans/2026-11-12-permission-allow-list/`). Reviewer ran the Python suite (580 OK) and node (15 pass), in-memory `check_probe` checks; `git status` identical before and after. Note: the Orchestrator appended one line to `log.md` right after starting the review (a plan file inside the scope) — recorded in the log.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | High | `update` (and `get`/`exec`) can target an id the probe did not create: a `save` name equal to a built-in variable (`admin_uid`, `today`, `group_<role>` …) passes the loader, a `create` with `expectHttp` counts as a save, saves are carried across specs while run-time variables are per spec → `POST /api/items/<admin uid or group id>/update` with the administrator's key | Fixed: loader refuses reserved save names, does not count a refused create, keeps saves per spec; runner (`pls_http.run_tests(confine=True)` from kb-verify) refuses a record op on an id not returned by a create of the same spec. Tests |
| F2 | Low | `finally` teardown substitution can raise `KeyError` outside the `try` when a further site was never created → run aborted, main site not deleted | Fixed: a teardown that names a site not created is saved empty (harmless) and logged; delete still runs. Test |
| F3 | Low | step `site` not a string (list) → `TypeError` instead of a refusal | Fixed: refused with `ValueError`. Test |
| F4 | Low | unknown `${probe_site:…}` in `expect_stored` not refused at load | Fixed: `expect_stored` scanned too. Test changed accordingly |
| F5 | Low | probe file named `X__k` collides with probe `X`'s site `k` | Fixed: probe file names with `__` refused. Test |
| F6 | Low | `expect_stored` main-site-only limit not in tech-debt | Fixed: TD-44 |
| F7 | Low (pre-existing) | literal site ids in probe settings (Summaries, Links, `[[n]]`) not checked; a probe could write into an app site via a Summary | Recorded: TD-45 (review of the probe file is the control until then) |
| F8 | Low | D39 / schema.md say Crosstab names are not in the source notes; hand-over cites `View.cs` | Fixed: names and lines added to `source-notes.md` (read from the clone); KB wording by the curator |

## Round 2 (pls-x-reviewer, opus, high, 2026-11-14) — verdict: accept with fixes

All round-1 dispositions hold (F1 also: `IssueModel.SetByApi` does not set `SiteId`, so an update cannot move a record). Criteria 1–6 met (criterion 5 checked by the reviewer: parent modules, 16 tests → 9 failures, 7 errors). `git status` identical before and after.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| L1 | Low | F5 incomplete: probe `X_` + key `k` and probe `X` + key `_k` share title/state `X___k` | Fixed: site keys `^[a-z0-9]+(_[a-z0-9]+)*$`; probe file names may not start or end with `_`. Test |
| L2 | Low | confirmation counts probes, not sites (20 probes, 23 sites) | Fixed: prompt names the number of sites and probes |
| L3 | Low | `$group_<role>` accepted in `exec` data, but exec data is not substituted | Fixed: `$` variables refused in exec data at load. Test |
| L4 | Low | `skills/pls-x-lifecycle/references/kb-gaps.md` step 4 does not name ADR-0026 capabilities | Deferred: a lifecycle skill text change needs its eval run (HANDOFF "How we work"); follow-up in HANDOFF, with the next lifecycle change |
| L5 | Low | ADR-0026 Option B text tightened after Nam accepted it (Decision unchanged) | Reported to Nam in the task report; text kept (it only narrows what a probe may do) |
| info | — | `ReferenceType` of a site not type-checked | Not changed: a wrong value fails `createsite` on the probe folder only |
