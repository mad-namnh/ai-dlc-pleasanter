# Plan — `pls scope` report (settings coverage WS6b)

- **Date / branch / parent commit:** 2026-11-16 / `brownfield-adr` / `f3a460c`
- **Objective:** per site, read from git, the keys and dashboard types without round-trip evidence, so P2 / P3 see at design time what `release-plan` would refuse. Output follows `pls_scope.unverified`.
- **Tier:** Standard (local, read-only command).
- **Scope:** subcommand `scope [--site S]` (local, no network); exit 1 while any finding; architecture command row; classified LOCAL in the write-guard test.
- **Out of scope:** skill text (TD-65, eval needed).
- **Stop points:** none.
- **Acceptance criteria:**
  1. Lists, per site, the same findings `pls_scope.unverified` gives for git settings and scripts; "no finding" for a clean site.
  2. `--site` limits to one site; an unknown site is a refusal; exit 1 with findings, 0 without.
  3. New test fails on the parent; suites green (3.12, 3.10, node).
  4. Review: no open Critical / High.
- **Subagents:** `pls-x-reviewer` (sonnet, medium).
- **Documents:** architecture command table; TD-65; HANDOFF line.
