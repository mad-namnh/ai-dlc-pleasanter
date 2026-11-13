# ADR-0020: Gate records, approvers and profile records

- **Status:** Proposed (2026-11-11) — describes what `pls` does today; Nam accepts, changes or rejects it. Once accepted it replaces the "Implementation notes (2026-11-09)" of ADR-0012, which were added after that ADR was accepted
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

**Profile records (guard inputs outside the four gates).** The profile rows **Approvers**, **Operators**, **Origin** and the `role` of an environment are set only through `pls profile set`, which records the person's words under `gates/profile/` and then writes the file; once a field has a record, the recorded value is the one `pls` reads, and lint L-PRF-01 reports a row that differs from its record or has none, and a stg / prod role without a record (`tools/pls/pls_profile_records.py`, roadmap P0-4). `pls init --approver` records the values the person typed on the command line.

**Manual deploy of scheduled scripts** (ADR-0012 option B). `pls jobs-verified <R> --by <name> --quote "…" [--approved-by <G4 approver>]` records in `plan.jobs.verified` who copied and checked the scripts. `--by` must be an **operator of the release's environment** (profile row **Operators**, e.g. `dev: Nam; stg: Nam; prod: <customer operator>`) or a **G4 approver**; a profile without an Operators row accepts G4 approvers only (`pls_gate.py` `operators`, `job_verifier`). The record is checked again when it is used. Until a release's job changes are verified they are listed again by the next release.

**As-is review record** (`pls review as-is`, skill `pls-x-spec-recovery`): the reviewer must be a G2 approver (`tools/pls/pls_as_is_review_records.py`).

**Onboarding first** (taken-over apps). When the profile row Origin is `existing` and there is no `ops/onboarding/*-summary.md`, `pls step` for a change phase (P1–P5, G1–G4), `pls gate`, `pls bootstrap-plan` and `pls release-plan` refuse, and lint L-ONB-01 reports REQ / DES documents (`pls_gate.py` `require_onboarding`, `pls.py` `need_onboarding`).

## Open questions

- [ ] Who approves G4 for a customer staging environment and for production: one approver named in the profile (as built), or two (customer business owner **and** operator, as the gate table of `docs/architecture.md` §4 has said since v0.1)? — *Nam, before the first `cstg` project*
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

**Proposed: option C.** The model "As built" holds for stage `demo`. The approver rule for `cstg` and `prod` is the first open question and is decided before the first `cstg` project.

When accepted:
- this ADR is the source for gate records, approvers, profile records, `jobs-verified` roles and the onboarding-first refusal; `docs/architecture.md` I4 and §4 point here;
- the "Implementation notes (2026-11-09)" of ADR-0012 are replaced by the section "Manual deploy of scheduled scripts" above (ADR-0012's Status line then names this ADR — a change Nam makes).

## Consequences

- Easier: a change to who may approve, or to which command needs which record, is now a change to this ADR, visible in review.
- Harder / costs: option B, if chosen, changes the record model and every G4 check, and needs a second approver in the profile of every customer project.
- Follow-up: Nam decides the open questions before `cstg`; the gate table of `docs/architecture.md` §4 keeps the target approvers until then and says what is enforced today.
