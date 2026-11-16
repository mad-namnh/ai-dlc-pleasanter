# Plan — departments in `pls principals` (settings coverage WS4.2)

- **Date / branch / parent commit:** 2026-11-16 / `brownfield-adr` / `954499f`
- **Objective:** a role of `design/roles.json` with `"principal": "Dept"` is bound to `Dept,<id>` per environment, so `${principal:x}` resolves for departments (ADR-0006 already names `Dept,<id>`).
- **Tier:** Standard (read-only lookup; no new write path).
- **Scope:** `bind_principals` lookup through `/api/depts/get` by `dept_code` (preferred) or `dept_name`, exact match, ambiguity refused, failed lookup refused; departments never created (also not with `--create`). Fake server answers `/api/depts/get`.
- **Out of scope:** creating departments (the plan's "`--create` on dev only, like groups" would be a new write path outside ADR-0017 — not built; departments are the customer's organisation); P2 skill text (TD-64).
- **Stop points:** none.
- **Acceptance criteria:**
  1. Code and name lookups bind exactly (a like-matching neighbour is ignored).
  2. Missing department → reported (exit 1), nothing written, also with `--create`.
  3. Ambiguous match and failed lookup → refusal.
  4. New tests fail on the parent; suites green (3.12, 3.10, node).
  5. Review: no open Critical / High.
- **Subagents:** `pls-x-reviewer` (sonnet, medium — Standard).
- **Documents:** ADR-0006 as-built line; TD-64; HANDOFF line.
