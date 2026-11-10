# Plan — P3-1: architecture §7.1 / §7.2 checked by a test against the parser and the lint rule codes

- **Date / branch / parent commit:** 2026-11-11 / `brownfield-adr` / `846790a`
- **Objective:** A test in `tools/pls/tests` fails when `docs/architecture.md` §7.1 (command table) or §7.2 (lint rule catalogue) names a command or lint rule `pls` does not have, or misses one it has. The document is aligned where the test shows a difference.
- **Tier:** Standard (`CLAUDE.md` "Adaptive Model Routing") — a new test, a document alignment and one behaviour-preserving extraction in `pls.py`; no guard, gate, permission or secret is touched.
- **Scope:**
  - `build_parser()` extracted from `_main` in `tools/pls/pls.py` (same parser, same arguments), so a test can read the commands from the parser itself.
  - New test: commands of the parser == commands named in the first column of the §7.1 table; rule codes `pls lint` can emit == rules of the first table of §7.2. Emitted codes are read from the source with `ast`: every dict literal with a `"rule"` key in `tools/pls/*.py`; a non-literal value must be a parameter of a local helper whose calls pass literals, anything else fails the test.
  - `docs/architecture.md` §7.1 and §7.2 aligned.
- **Out of scope:** §3.2 (also named by roadmap item P3-1, not by this task); sub-actions of a command (`skills check|sync`, `profile set`, …); the Phase / Purpose / Status text of the rows; the rule list in the `pls.py` module docstring and in the `pls lint` row; `pls deploy` in §3.3.
- **Files:** `tools/pls/pls.py`, `tools/pls/tests/test_architecture_tables_match_the_parser_and_lint_rules.py`, `docs/architecture.md`, `HANDOFF.md`, this folder.
- **Invariants and ADRs touched:** none.
- **Stop points expected:** none. (`.claude/settings.json` shows an uncommitted change: Nam's own deny rules for `git -C`, announced by him; not touched, not committed by this task.)
- **Acceptance criteria:**
  1. The new test fails when §7.1 names a command the parser does not have, and when it misses a parser command.
  2. The new test fails when the §7.2 lint catalogue names a rule `pls lint` cannot emit, and when it misses one it can emit.
  3. The source of truth is the parser of `tools/pls/pls.py` and the rule codes in the issues lint builds — no second hand-kept list in the test.
  4. The new test fails on the parent commit and passes after the change.
  5. Both suites pass (Python on the current version and on 3.10; node).
  6. No command changes behaviour; no guard, gate, permission or protected path is touched.
- **Tests:** the new test file (4 tests: commands, lint rules, and two that show a deliberately wrong table is reported); full Python suite on 3.12 and 3.10; node suite; the new test file run on a worktree of `846790a`.
- **Subagents planned:** `pls-x-reviewer` on `sonnet`, effort `medium` (Standard change) — one round, a second only for Critical / High findings.
- **Documents to update in the same commit:** `docs/architecture.md`, `HANDOFF.md` (progress, test count).
