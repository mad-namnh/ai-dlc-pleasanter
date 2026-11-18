# ADR-0020: Gate records, approvers and profile records

- **Status:** Accepted (2026-11-18, Nam: "chấp nhận ADR20") — option C, with the team rules of "As built" (2026-11-18). Replaces the "Implementation notes (2026-11-09)" of ADR-0012
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** I4 (`docs/architecture.md` §2), §4 gate table; ADR-0004, ADR-0012, ADR-0014 (TB-1, TB-2, TB-3); design review 2026-11-09 A2 items 1–3, A3, A4 item 1 (`docs/reviews/design-review-2026-11-09/ws-1-architecture.md`); roadmap P0-1, P0-3, P0-4, P2-6

## Context

Invariant I4 says people approve at gates G1–G4 and the AI never approves its own work. Since slice #3 the rule is enforced by `pls`: gate decisions are files under `gates/`, and several commands refuse to write without the matching record. The design review of 2026-11-09 found that this model was built without an ADR (A2 item 1), that the rules for who confirms a manual deploy of scheduled scripts were added as notes to the Accepted ADR-0012 (A2 item 2, A3), that the onboarding-first refusal lived only in a skill (A2 item 3), and that `docs/architecture.md` still said gate decisions are recorded in `releases/R-*/approvals.md` and that G4 needs two people (A4 item 1).

This ADR writes the model down as built, so that a change to it is a decision, and names the points that are still open.

## As built (2026-11-11, `pls` on `brownfield-adr`)

**Records.**
- `pls gate <G> --decision approved|rejected|changes-requested --approver <name> --quote "<their words>" (--item ID … | --release R …)` writes one JSON file per decision under `gates/` (project root), named `<date>-<gate>-<hhmmss>-<random>.json`, opened with exclusive create — a record is never overwritten (`tools/pls/pls_gate.py` `record`). G1 / G2 name the REQ / DES ids they decide; G3 / G4 name release ids (G4 also bootstrap ids).
- Fields: `gate`, `decision`, `approver`, `date`, `at` (ISO instant with UTC offset), `quote` (required, not empty), `items`, `releases`, `recorded_by`; an approved G4 also stores `bound`: the digest of each named release's planned content and migration folders (`pls_release_digest`, roadmap P0-1).
- The approver must be listed for that gate in the profile row **Approvers** of the project `CLAUDE.md` (`_approver_for`); the name is checked again whenever a record is used, so a hand-written record by anyone else does not count (`require`).
- **Last decision counts:** per gate and item / release, the record with the latest instant in `at` wins; on the same instant any decision other than `approved` wins (`latest`). A record that cannot be read, has the wrong shape, or is dated more than 5 minutes in the future makes every gate check refuse until a person repairs or removes it (`load`, `_record_problem`).
- `releases/R-*/approvals.md` is a note for people. The records `pls` checks are only those in `gates/`.

**Where a record is required** (outside `role: dev`, except `pls package`, which needs G4 in every environment; on dev no other gate record is checked):

| Command | Record | Code |
|---|---|---|
| `pls release-plan` for a non-dev environment | G3 approval of the release | `tools/pls/pls.py` (`GT.require(r, "G3", …)`) |
| `pls apply`, `pls bootstrap`, `pls migrate` on a non-dev environment | G4 approval of the release / bootstrap id, bound to its content (a release changed after G4 is refused) | `pls.py` (`GT.require(r, "G4", …)` in apply, bootstrap, migrate) |
| `pls test` with specs that change records outside dev | G4 of the release under test (`--release`, same environment), or the person's confirmation of this run: the environment name typed at a terminal, or `--yes` given on their instruction (`_confirm`) — **no gate record in that case** | `pls.py` (test command) |
| `pls package` (production hand-over, ADR-0003), any environment | G4 approval bound to the content | `pls.py` (package command) |
| lint L-GATE-01 | every "G<n> approved" status line in a REQ, DES, G3 or approvals file has a matching record by a profile approver | `pls_gate.py` `lint` |

One approver per record. The profile decides who may approve which gate (`Nam (all gates)`, `Nam (G1, G2), Taro (G3, G4)`, `G1, G4: Nam; G2, G3: Taro`). No gate requires two records.

**Team approvers and G4 delegation (2026-11-18, team rollout decisions N3–N8 of Nam).** A range before the colon grants only that range (`G1–G3: A, B; G4: Nam`; a head that is not a list of gates grants nothing — it once gave every listed name all four gates). A grant may carry its last day, inclusive, in the approver's local date: `G4 until 2026-12-05: Taro` or `Taro (G4 until 2026-12-05)`; after that day the grant is gone, an `until` without a valid date grants nothing (`tools/pls/pls_gate.py` `grants`, `approvers`). A gate record (and a `jobs-verified` confirmation) counts when its approver held the gate **under the Approvers value in force at the record's instant and on its day** (`pls_profile_records.effective_profile_text(at=…)`), so a release a delegate approved during the delegation stays approved after the delegation ends or is removed from the row, and so does one approved by a person later removed from the row; to undo an approval the owner records a later decision (`rejected` / `changes-requested`: the last decision counts). `pls gate` refuses a delegate after the last day (`require`, `validate`). (Nam, 2026-11-18, review finding F1 option a.) The names holding G4 without an end date are the **owners** (`owners`). A dev may approve the gates of their own task (N4); the customer approves no gate (N5).

**Who changes Approvers, Operators and an environment's role.** Only an owner (`tools/pls/pls_profile_records.py` `_check_owner`): a G1–G3 approver or a time-boxed delegate cannot widen their own rights, give themselves G4, name themselves stg operator, or make stg count as dev (a `role: dev` environment needs no G4). A hand edit of `environments.json` that makes a role differ from its record stops every command that reads the environment until the file is restored or the owner records the role (`pls.py` `role_record_problem`, Nam 2026-11-18, review finding R2-4 option a); an environment that has no role record (dev entries made by setup, init, sandbox create) is still read from the file. In a new Approvers value a G4 grant to a name that is not an owner already must carry an end date (only the owner delegates, and a delegation ends by itself), the value keeps at least one owner, and no grant ends in the past; the first Approvers value makes the person stating it an owner. A profile that names approvers but no owner refuses every change of these rows and lint L-PRF-01 reports it; the person repairs it once by hand by **adding** one Approvers record that names an owner (earlier records stay: approvals are judged by the profile of their time) — otherwise a G1–G3 approver could make themselves the owner (Nam, 2026-11-18, review findings F3 option a and R2-6). A value is a **first value** only while there is no Approvers record and the row grants nothing (the template placeholder); a recorded value, or a row whose grants have all ended, never is (review finding R2-3). A gate record older than the first Approvers record is judged by the current row of `CLAUDE.md` (no earlier record exists). Through `pls` the set of owners can only shrink: a second owner or a hand-over is refused (a G4 grant to a new name needs an end date). An end date written after a name (`Taro until 2026-12-05`) grants nothing; so does a name holding a date or a colon (`dev01` is a name). An `until` applies to every gate of its group: `Taro (G1–G3, G4 until D)` ends all four on D. A former delegate can hand-write a backdated record in their own name, as anyone can hand-write a record naming an approver — the trust TB-3 describes, not something `pls` tells apart. The real control for writes to stg is the stg write key, which only the owner or a delegate holds (`.pls/connections.json` with `allow_write`, ADR-0021); gate and profile records live in git and are trusted as TB-3 says.

**Profile records (guard inputs outside the four gates).** The profile rows **Approvers**, **Operators**, **Origin**, **Role tests** and the `role` of an environment are set only through `pls profile set`, which records the person's words under `gates/profile/` and then writes the file; once a field has a record, the recorded value is the one `pls` reads, and lint L-PRF-01 reports a row that differs from its record or has none, and a stg / prod role without a record (`tools/pls/pls_profile_records.py`, roadmap P0-4). **Role tests** (`deferred` / `per-role keys`) is recorded because deferring role tests lowers what G3 proves. For Role tests no pls command reads the row (the skills do): its record gives tamper evidence — L-PRF-01 reports an unrecorded, unknown or differing row — not enforcement. `pls init --approver` records the values the person typed on the command line (Role tests from `--stage`).

**Manual deploy of scheduled scripts** (ADR-0012 option B). `pls jobs-verified <R> --by <name> --quote "…" [--approved-by <G4 approver>]` records in `plan.jobs.verified` who copied and checked the scripts. `--by` must be an **operator of the release's environment** (profile row **Operators**, e.g. `dev: Nam; stg: Nam; prod: <customer operator>`) or a **G4 approver**; a profile without an Operators row accepts G4 approvers only (`pls_gate.py` `operators`, `job_verifier`). The record is checked again when it is used. Until a release's job changes are verified they are listed again by the next release.

**As-is review record** (`pls review as-is`, skill `pls-x-spec-recovery`): the reviewer must be a G2 approver (`tools/pls/pls_as_is_review_records.py`).

**Onboarding first** (taken-over apps). When the profile row Origin is `existing` and there is no `ops/onboarding/*-summary.md`, `pls step` for a change phase (P1–P5, G1–G4), `pls gate`, `pls bootstrap-plan` and `pls release-plan` refuse, and lint L-ONB-01 reports REQ / DES documents (`pls_gate.py` `require_onboarding`, `pls.py` `need_onboarding`).

## Open questions

- [ ] Who approves G4 for a customer staging environment and for production: one approver named in the profile (as built), or two (customer business owner **and** operator, the earlier target of `docs/architecture.md` §4)? — *Nam, with the customer deployment mechanism (N16)*
- [ ] Are gate records protected beyond git for `cstg` / `prod` (ADR-0014 open question 1)? — *Nam, before the first `cstg` project*

## Options

### Option A — One approver per record; the profile names who approves which gate (as built)
- Pros: built and tested; works for the demo stage, where Nam approves every gate; several approvers are expressed through the profile (one per gate).
- Cons: a single person can approve a production-bound release; the architecture's "owner + operator" for G4 is not enforced.

### Option B — G4 outside dev needs two records: an approver from the customer side and an operator
- Pros: matches the gate table of `docs/architecture.md` §4; no single person can release to stg / prod.
- Cons: not built (record model, profile rows and every G4 check change); no second person exists in the demo stage.

### Option C — A for stage `demo`; B, or another rule Nam decides, before the first `cstg` project
- Pros: keeps what works now and makes the gap a dated decision, not a silent difference between documents.
- Cons: the decision for `cstg` is still to be taken.

## Decision

**Accepted: option C** (Nam, 2026-11-18). The model "As built" holds for stage `demo` and for MADLAB's own dev and stg in stage `project`: every dev approves G1–G3, their own tasks included; G4 has one owner who delegates it only with a last day; the customer approves no gate (team rollout decisions N3–N8, `plans/2026-11-18-team-rollout-after-freeze/plan.md`). The approver rule for a customer's `cstg` and `prod` stays the first open question; it is decided with the customer deployment mechanism, built only when Nam asks (N16).

With the acceptance:
- this ADR is the source for gate records, approvers, profile records, `jobs-verified` roles and the onboarding-first refusal; `docs/architecture.md` I4 and §4 point here;
- the "Implementation notes (2026-11-09)" of ADR-0012 are replaced by the section "Manual deploy of scheduled scripts" above (ADR-0012's Status line names this ADR, recorded with this acceptance).

## Consequences

- Easier: a change to who may approve, or to which command needs which record, is now a change to this ADR, visible in review.
- Harder / costs: option B, if chosen, changes the record model and every G4 check, and needs a second approver in the profile of every customer project.
- Follow-up: Nam decides the open questions before `cstg`; the gate table of `docs/architecture.md` §4 keeps the target approvers until then and says what is enforced today.
- Amended (2026-11-16) by ADR-0029 B: a G1 / G2 approval is refused while `pls check p1` / `p2` reports a finding for an approved item (or an item with no document, a misnamed document, or — G2 — a G1-approved REQ without a DES), unless `--accept-findings "<reason>"`; the record then holds `accepted_findings` and `accept_reason`. Rejections are never refused.
- Amended (2026-11-18) by ADR-0029 B (TD-67): a G2 approval binds the content (sha256) of each DES it approves (`bound_des`), so an edited DES is not taken for the approved one. A G3 approval names the target (`--env`, kept in the record as `env`) and the DES the release ships (`--item`); it is refused while the built change disagrees with them (`pls check p3 --env --des`) or when either is missing, unless `--accept-findings "<reason>"`, recorded the same way. `release-plan` on a non-dev target refuses a G3 whose `env` is another target.
