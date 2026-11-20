# Plan — phase 6: CI for both suites

- **Date / branch / parent commit:** 2026-11-18 / `brownfield-adr` / `2e869bb`
- **Objective:** every push and pull request to the framework repository runs both suites and the impact-rules freshness check on GitHub Actions, so "CI green on the tag" (definition of done, criterion "stable") can be checked.
- **Tier:** Standard (`CLAUDE.md` "Adaptive Model Routing") — new multi-file tooling, no guard, gate or secret touched.
- **Scope:** `.github/workflows/framework-ci.yml`; a test that keeps the workflow tied to the documented commands and the minimum Python; docs that say CI is missing or 3.10 lives in a temporary folder.
- **Out of scope:** branch protection / required checks on GitHub (Nam's settings, with TD-17); CI inside customer project repositories (architecture §P4 "Checks", not built); pinning actions by commit SHA (cannot be verified offline here — recorded as a limit).
- **Files:** `.github/workflows/framework-ci.yml`, `tools/pls/tests/test_framework_ci_workflow.py`, `docs/architecture.md`, `docs/adr/0016-agent-team-for-framework-development.md` (Limits only), `HANDOFF.md`, this plan's `plan.md` phase table, `log.md`.
- **Invariants and ADRs touched:** none (ADR-0016 Limits bullet on Python 3.10 updated, not its Decision or Status).
- **Stop points expected:** item 4 — the workflow only runs after Nam pushes; the agent does not push.
- **Acceptance criteria:**
  1. The workflow runs on push to `main`, `brownfield-adr`, tags `v*`, and on pull requests; read-only `contents` permission.
  2. Python suite on Ubuntu with Python 3.10 and 3.12, and on Windows with 3.12 (the team's machines; Git Bash hook tests run there).
  3. Node is installed in every Python job, so the three node-dependent tests and lint L-SCR-02 run instead of skipping.
  4. `node --test tools/pls/tests/test_runner.mjs` runs.
  5. The impact-rules freshness check regenerates the file and fails on a difference, with the regenerate command in the message.
  6. Full history is checked out (`fetch-depth: 0`) so the fix-commit check of the suite runs instead of skipping.
  7. A unit test fails when the workflow is missing, drops 3.10 / the minimum Python of `pls.py`, drops one of the commands or the full-history checkout.
- **Tests:** new `test_framework_ci_workflow.py` (fails on the parent: no workflow); both suites on Windows 3.12 and 3.10; the workflow's commands run by hand on Linux (WSL Ubuntu 24.04, Python 3.12, clone of the commit).
- **Subagents planned:** `pls-x-reviewer`, sonnet, effort medium (Standard).
- **Documents to update in the same commit:** architecture §7 portability + I7 row note, ADR-0016 Limits (3.10), HANDOFF "Resume here" + "How we work", rollout plan phase table.
