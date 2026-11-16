# Plan — Product specification and ADRs for the lifecycle console (control plane, UI, worker)

- **Date / branch / parent commit:** 2026-11-13 / `brownfield-adr` / `c7d8d36`
- **Objective:** Turn the agreed discovery (`docs/product-discovery/`, decisions Q1–Q16, H1–H5, concept C1) into a product specification and four Proposed ADRs, so that Nam can accept or reject each decision before any code is written.
- **Tier:** Critical — architecture and ADRs; one ADR changes who writes gate records (I4, ADR-0020, ADR-0014 TB-2).
- **Scope:**
  - commit 1: `docs/product-discovery/` as it stands (discovery record);
  - commit 2: `docs/product/console-spec.md`; ADR-0026 (product and architecture), ADR-0027 (gate records written by the control plane under an authenticated user), ADR-0028 (run segments and Human Requests), ADR-0029 (trust of a worker checkout); `docs/adr/README.md` rows; one "planned, not built" line in `docs/architecture.md`; `HANDOFF.md` resume note.
- **Out of scope:** code; choosing the frontend stack (left open in ADR-0026, Nam 2026-11-13); creating the new repository; changing any skill, `pls` command or existing ADR (changes are proposed inside the new ADRs, not applied).
- **Files:** as in Scope.
- **Invariants and ADRs touched:** I3, I4, I6, I7, I8 (described, not changed); ADR-0013, ADR-0014, ADR-0020, ADR-0022 (amendments proposed in the new ADRs only).
- **Stop points expected:** none while writing (all new ADRs are Proposed; accepting them is Nam's, stop point 1). No protected path is edited.
- **Decisions by Nam before the work (2026-11-13):** code in a separate repository; four separate ADRs; stack left open in the spec; two commits.
- **Acceptance criteria:**
  1. The spec covers users and jobs, journeys, the CR and its two axes, Human Requests, screens W1–W3, MVP in / out, non-functional and security requirements, and every requirement traces to a decision (Q / H) or a cited framework fact.
  2. Each ADR follows `docs/adr/0000-template.md`, has Status Proposed, names the ADRs it amends without editing them, and lists open questions with who answers them.
  3. No claim about the framework that the code does not support; nothing says a feature exists that is not built.
  4. No customer data, names, site names or URLs; English only (Japanese only as UI labels where needed).
  5. `docs/adr/README.md` lists 0026–0029; `docs/architecture.md` tests still pass.
  6. Both suites green before each commit.
- **Tests:** no code change; run `python -m unittest discover -s tools/pls/tests` and `node --test tools/pls/tests/test_runner.mjs` (architecture tables and layout tests read the docs).
- **Subagents planned:** `pls-x-reviewer` on commit 2 (opus, effort high — Critical tier).
- **Documents to update in the same commit:** `docs/adr/README.md`, `docs/architecture.md`, `HANDOFF.md`.
