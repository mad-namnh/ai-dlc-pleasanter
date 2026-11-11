# Plan — P3-1 (rest): architecture §3.2 checked by a test against what pls creates and names

- **Date / branch / parent commit:** 2026-11-11 / `brownfield-adr` / `7f4fba3`
- **Objective:** A test in `tools/pls/tests` fails when the project layout of `docs/architecture.md` §3.2 and reality differ. The document is aligned where the test shows a difference.
- **Tier:** Standard (`CLAUDE.md` "Adaptive Model Routing") — a new test and a document alignment; no code of `pls` changes; no guard, gate, permission or secret is touched.
- **What "reality" is (decided here, Nam may change):** three sources that can be read without a hand-kept copy of the layout:
  1. what `pls init` creates in an empty folder (`pls.init_project`, run by the test in a temporary folder);
  2. the names `pls` joins into a path with `/` in `tools/pls/*.py` (read with `ast`: text constants and f-string shapes);
  3. for the opposite direction only: names in any text constant of `tools/pls/*.py`, and names in `code` spans of `skills/**/*.md` and `templates/project/CLAUDE.md` (files written by a skill, not by `pls`).
- **Scope:**
  - New test file with three checks: (A) every path `pls init` creates is in the tree, at the same place; (B) every path name of source 2 is a name in the tree, or is listed in the test with the reason it is not part of a project; (C) every name in the tree without a placeholder is created by `pls init` or named by source 2 or 3.
  - `docs/architecture.md` §3.2: the tree is rewritten to one name per line and aligned; items that nothing creates or names leave the tree and stay in a "planned, not built" sentence (as `validate` did in §7.1).
- **Out of scope:** the comments of the tree lines; where in the tree a name of check B sits; names with a placeholder in check C; paths `pls` builds without `/` (a text constant such as `gates/review`, a glob) in check B; `templates/project/CLAUDE.md` "Layout" table (protected path).
- **Files:** `tools/pls/tests/test_architecture_project_layout_matches_what_pls_creates_and_names.py`, `docs/architecture.md`, `HANDOFF.md`, this folder.
- **Invariants and ADRs touched:** none.
- **Stop points expected:** none.
- **Acceptance criteria:**
  1. The test fails when §3.2 misses a path that `pls init` creates.
  2. The test fails when §3.2 misses a path name that `pls` joins into a project path, unless the test lists that name with a reason.
  3. The test fails when §3.2 names a file or folder (without a placeholder) that neither `pls init`, the `pls` sources, a skill nor the project template names.
  4. The sources of truth are read from the code, the skills and the template — the test holds no copy of the layout; the only hand-kept list is the names that are not part of a project, each with its reason.
  5. The new test fails on the parent commit and passes after the change.
  6. Both suites pass (Python on the current version and on 3.10; node).
  7. No command changes behaviour; no guard, gate, permission or protected path is touched.
- **Tests:** the new test file; full Python suite on 3.12 and 3.10; node suite; the new test file run on a worktree of the parent commit.
- **Subagents planned:** `pls-x-reviewer` on `sonnet`, effort `medium` (Standard change) — one round, a second only for Critical / High findings.
- **Documents to update in the same commit:** `docs/architecture.md`, `HANDOFF.md` (progress, test count).
