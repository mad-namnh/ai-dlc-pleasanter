# ADR-0024: Standing permission for writes to dev, recorded once per project

- **Status:** Accepted (2026-11-12, Nam) — option B; built with AU3
- **Date:** 2026-11-12
- **Deciders:** Nam
- **Related:** I3, I4 (`docs/architecture.md` §2); ADR-0008 (write guard, typed confirmation), ADR-0014 (TB-2 actor and confirmation, TB-3 records), ADR-0020 (gate records and approvers), ADR-0021 (write opt-in per machine); `CLAUDE.md` Mandatory 1 ("Agents must not add `--yes` unless the user asks for it"); project template `CLAUDE.md` hard rule 3; `docs/plan.md` Step 4d **AU3**; origin: trial `pls-demo-contracts`, 2026-11-11

## Context

From a specification to a running app on dev, the trial needed a person outside the gates every time `pls` wrote to dev: `bootstrap`, `apply` and `migrate` ask the person to type the release id at a terminal (`_confirm` in `tools/pls/pls.py`), or the person tells the agent to add `--yes` for that target. In a P3 loop (apply → round trip → fold back → apply again) that is several stops per change request, each one only repeating a choice the person has already made: "the agent may write to my dev".

What holds today and does not change with any option below:
- `pls` writes only to `role: dev`, or `stg` after G4; `role: prod` is never written (`assert_writable`, ADR-0008);
- the operator's local opt-in `allow_write: true` (ADR-0021, asked by `pls setup` since 2026-11-12);
- the gates G1–G4 (I4); G4 and a recorded G3 for stg; side-effect and jobs refusals (ADR-0010, ADR-0012); stale-plan and per-site guard checks (P3-7);
- `apply` re-checks the guard before every site (P3-7).

What the typed confirmation adds on dev: a person sees each write before it happens. What it costs: the person must be at a terminal for every dev write, so a spec cannot become an app on dev without them outside the gates.

## Open questions

- [x] Which commands does the permission cover? — only `bootstrap`, `apply`, `migrate` (Nam, 2026-11-12)
- [x] Does the permission expire, or hold until it is revoked? — until revoked (option B, Nam, 2026-11-12)
- [x] Does a sandbox need its own record? — yes, one record per sandbox (Nam, 2026-11-12)
- [ ] `CLAUDE.md` Mandatory 1 and the project template hard rule 3 (protected paths) must name the exception; their wording is Nam's.

## Options

### Option A — Keep the typed confirmation (status quo)

Every dev write: the person types the release id, or tells the agent to add `--yes` for that target in the session.
- Pros: a person sees every write; nothing to build.
- Cons: AU3's aim is not met; `--yes` given in chat for a session is already a standing permission, but unrecorded (only the run log shows `confirmed: --yes`).

### Option B — A standing permission recorded once per project and dev environment, revocable (recommended)

- The person states it in their own words; the agent records it with `pls profile set dev-writes on --env dev --approver <name> --quote "<their words>"` (an approver of the profile, the same rule as `Approvers` / `Origin`; `gates/profile/dev-writes-dev-*.json`, created exclusively). `pls profile set dev-writes off --env dev …` revokes it; the latest record wins.
- While it is `on`, `_confirm` accepts the write **only** when all of these hold, checked by `pls` itself: the target's `role` is `dev` (never `stg`, never `prod`; a sandbox only if its own record or the `dev` record covers it — open question); the command is one of the covered ones; `allow_write` is true; every other refusal passed. The agent does not add `--yes`.
- The release folder and the run log record the confirmation as `standing permission (gates/profile/dev-writes-dev-….json, <approver>)` instead of `--yes` / `typed at a terminal` (ADR-0014 TB-2 evidence stays in the repository).
- Lint flags a hand-edited record (as L-PRF-01 does for the other profile rows).
- Pros: one recorded decision, in the person's words, replaces many repeated ones; stg and prod unchanged; the decision is visible and revocable in git.
- Cons: a person no longer sees each dev write before it happens; a wrong `role: dev` label on a non-dev server (ADR-0014 TB-10) is then written without a prompt — the remaining controls are `allow_write` asked per machine (ADR-0021) and the URL check in `http-check`.

### Option C — As B, with an expiry

As B, but the record carries `until` (a date, at most N days ahead; e.g. 14); after it, `_confirm` asks again.
- Pros: a forgotten permission ends by itself.
- Cons: one more decision (N); a long project re-records it periodically.

## Decision

**Option B**, accepted by Nam on 2026-11-12. His answers to the three questions asked (AskUserQuestion, 2026-11-12): "B: đến khi thu hồi (Recommended)"; "Chỉ bootstrap/apply/migrate (Recommended)"; "Mỗi sandbox một record (Recommended)".

- The permission holds until revoked; it covers `bootstrap`, `apply` and `migrate` on an environment whose `role` is `dev` (in `environments.json` and in its role record, if any); a sandbox needs its own record; `principals --create`, `test-users`, `test`, `kb-verify` keep their confirmation.
- It never applies to `stg` or `prod`, never replaces `allow_write`, a gate, or any refusal: it is checked only where the typed confirmation was asked.

## Consequences

- Easier: P3 on dev runs without a person between the gates (AU3 "done when": the trial's P3 runs on dev without a typed confirmation, and stg still refuses).
- Harder / costs: the dev write path loses its per-write human check; tests must show that stg, prod, a missing or revoked record, a hand-edited record and a non-covered command still need the typed confirmation. A Critical change (write guard): review on the strongest model.
- ADR-0008 (Proposed) still says apply / bootstrap always ask (its Decision section, lines about the typed confirmation): it changes only with Nam's decision on ADR-0008.
- As built (2026-11-12, after review): a record counts only while its approver is an approver of the profile; lint L-PRF-01 reports an `on` record whose approver is not. A record written by hand that names a current approver is **not** told apart from one written by `pls` — the same trust as gate records (ADR-0014 TB-3); option B's "lint flags a hand-edited record" holds only in that narrower sense. Deleting an `off` record silently restores an earlier `on` (TB-3). Recording `on` needs role dev both in `environments.json` and in the role record. How each run was confirmed: `apply-log.json` (apply), `bootstrap-log.json` (one entry per bootstrap run, outside the G4 digest so a partial stg bootstrap can be resumed under the same G4), the migration entry of `plan.json` `migrations_run` (migrate), and the run-log metric `confirmed`. The record names an environment, not a URL: an operator's connection for `dev` pointed at another server carries the permission with it (TB-10).
- Follow-up after a decision: build in `pls` (`profile set dev-writes`, `_confirm`, apply-log `confirmed`), lifecycle skill rule 3, `docs/setup.md`; patches for `CLAUDE.md` Mandatory 1 and `templates/project/CLAUDE.md` hard rule 3 (protected paths, Nam applies).
