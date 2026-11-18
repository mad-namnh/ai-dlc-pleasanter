# Plan — phase 7: `pls status`, golden path, docs clean-up

- **Date / branch / parent commit:** 2026-11-18 / `brownfield-adr` / `bb94661`
- **Objective:** a person or agent at any stop sees the open items and the next command (`pls status`), and a developer has one page from a fresh machine to a stg release (definition of done: "simple to operate", "team runs it alone").
- **Tier:** Standard — new read-only command, docs; no guard, gate or write path changed.
- **Scope:** `tools/pls/pls_status.py` (new), `pls status` in `pls.py`; `docs/golden-path.md` (onboarding checklist, change request in a sandbox, stg release, manual steps with their recording command); lifecycle skill 0.33 section 1 starts from `pls status`; README status; HANDOFF reduced to current state (history kept verbatim in `plans/handoff-history/`); setup.md pointer; CHANGELOG; TD-74.
- **Out of scope:** a command that writes `.pls/connections.json` for a cloned project (TD-74, decided: documented manual step during the freeze, built only if the phase 10 trial needs it); evals of the lifecycle skill (phase 8).
- **Decisions (Orchestrator, per Nam's instruction to decide and continue):**
  - "Next" order: unreadable gate records → profile / onboarding → unfinished releases → work furthest along first (finish work in flight before new work). Reason: an unfinished apply or a half-released change blocks drift baselines for everyone.
  - REQ → DES coverage also from `traceability.json` (projects before ADR-0029 B have no `reqs` front matter; TD-68).
  - Status never names a gate passed without its record and suggests `pls gate` only "after the person decides" (I4).
  - Exit 0 always: status reports, it does not check (`pls check` / `lint` decide).
- **Stop points expected:** none (template `CLAUDE.md` not touched).
- **Acceptance criteria:**
  1. `pls status` writes no file (test compares the tree before and after).
  2. A change is walked from a new project to a stg release, the "Next" line naming the right command at each stop (G1, P2, G2, P3 release-plan, dev apply, P4 check p3, stg release-plan, G4, stg apply, nothing open).
  3. A rejection, a DES edited after G2, an unfinished apply, an unreadable gate record, a taken-over app without onboarding and a pending request, a sandbox, and traceability links are each named.
  4. Architecture command table lists `status`; the golden path's commands exist in the parser with the arguments shown.
- **Tests:** `test_status_names_the_next_step.py` (fails on the parent: no `pls_status`); both suites, 3.12 and 3.10; `pls status` run on copies of the three `pls-demo-*` projects (without `.pls/`).
- **Subagents planned:** `pls-x-reviewer`, sonnet, medium.
- **Documents:** architecture §7.1, golden path, setup, README, CHANGELOG, skills/README, lifecycle SKILL.md, tech-debt, HANDOFF.
