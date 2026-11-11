# Plan — P2-6 ADR governance (design review A2, A3, A4)

- **Date / branch / parent commit:** 2026-11-11 / `brownfield-adr` / `3255e97`
- **Objective:** every architecture-level behaviour that `pls` has today is described by an ADR; the ADR index and `docs/architecture.md` match reality and point to the ADRs instead of restating them; the decisions only Nam can take are listed with a recommendation each.
- **Tier:** Critical — ADRs and architecture; the new ADRs describe gate records, approver rules and the write opt-in (`allow_write`).
- **Scope:**
  1. New ADR-0020 *Gate records, approvers and profile records* (as built: `gates/*.json`, one approver per record, last decision by instant, G3 for a non-dev release plan, G4 for apply / bootstrap / migrate / package / record-changing tests outside dev, G4 bound to the release digest; profile rows Approvers / Operators / Origin through `pls profile set`; `jobs-verified` roles; onboarding-first refusal). Options for the open points (single vs dual approver for G4 outside the demo stage). Proposed; when accepted it replaces the implementation notes added to Accepted ADR-0012 on 2026-11-09.
  2. New ADR-0021 *Machine setup profile, key files and environment overrides* (`pls setup` / `init --profile`, `~/.pls/profiles/`, `allow_write` default, `file:` key references, `PLS_CONNECTIONS`, `PLS_PROFILE_DIR`, `PLS_ACTOR`). Options for the default of `allow_write` (roadmap P3-7) and the key-file location.
  3. New ADR-0022 *Framework distribution* (launcher `pls.py`, `PLS_HOME`, `.claude/framework.lock`, `pls skills check|sync`, merge driver).
  4. `docs/adr/README.md`: new rows; a column saying what is built and relied upon, so a Proposed ADR that is in use is visible; statuses unchanged.
  5. `docs/architecture.md`: I4 and §4 name `gates/` and ADR-0020; I7 "enforced by" says what exists; §7.3 and §8 point to `skills/README.md` for versions instead of stale numbers; §10 points to the ADR index.
  6. `plans/2026-11-11-p2-6-adr-governance/decisions-for-nam.md`: one row per Proposed / partly accepted ADR with a recommendation (accept / accept with limits / keep proposed / supersede), plus ADR-0001's undecided Decision section and ADR-0012's notes.
  7. Proposed patch (protected path) for `CLAUDE.md` Mandatory rule 1: the spike-era wording (`config.json`, `scripts/common.py`) is marked as applying to `spike/round-trip/` only.
- **Out of scope:** accepting or changing the Status or Decision of any existing ADR (stop point 1); code changes to `pls` behaviour (P3-7 changes the `allow_write` default); `docs/tech-debt.md` and the findings register (P2-7).
- **Files:** `docs/adr/0020-*.md`, `docs/adr/0021-*.md`, `docs/adr/0022-*.md`, `docs/adr/README.md`, `docs/architecture.md`, docstrings of `tools/pls/pls_gate.py`, `pls_profile_records.py`, `pls_http.py` (`connections_file`), `pls.py` (launcher / setup comments) citing the ADRs, `HANDOFF.md`, this folder.
- **Invariants and ADRs touched:** I3, I4, I7; ADR-0008, ADR-0012, ADR-0014 (cross-references only).
- **Stop points expected:** 1 (accepting ADRs — listed for Nam, not done); 3 (`CLAUDE.md` Mandatory — patch only).
- **Acceptance criteria:**
  1. Each of the seven A2 items has a Proposed ADR whose "as built" section matches the code (`file:line` cited) — item 3 (onboarding refusal) and item 2 (Operators) inside ADR-0020; 4–6 inside ADR-0021; 7 inside ADR-0022.
  2. No existing ADR file has a changed Status line or Decision section (`git diff --stat docs/adr/00[01]*.md` shows no change to 0001–0019).
  3. `docs/adr/README.md` lists 0001–0022; for every ADR the "Built" column agrees with the code.
  4. `grep -n "approvals.md" docs/architecture.md` returns no line that calls it the gate record; I4 names `gates/` and ADR-0020.
  5. §7.3, §8 and §10 of `docs/architecture.md` hold no version number that differs from `skills/README.md` and list no subset of ADRs as "the" related decisions.
  6. `decisions-for-nam.md` has one row per ADR whose status is not Accepted, each with a recommendation and its reason.
  7. The `CLAUDE.md` patch passes `git apply --check`.
  8. Both suites green (no behaviour change expected; docstring edits only).
- **Tests:** none new (documentation and docstrings). Python suite and node suite before each commit.
- **Subagents planned:** `pls-x-reviewer`, model `opus`, effort `high` (Critical tier), one round after all parts, a second only if needed.
- **Documents to update in the same commit:** the ADRs, ADR index, `docs/architecture.md`, `HANDOFF.md`.
- **Commits:** P2-6 in parts: (1) ADR-0020; (2) ADR-0021; (3) ADR-0022; (4) index, architecture, decisions list, patch, HANDOFF. Review after part 4 over the whole range; fixes as a fifth commit.
