# Plan — P2-7 tech debt and findings trace (design review H4, B9, J4)

- **Date / branch / parent commit:** 2026-11-12 / `brownfield-adr` / `b45bc3b`
- **Objective:** every open review item has a tech-debt line with a deadline; every row of the findings register names its artefact (Trace column); KB findings D21–D33 are in the register.
- **Tier:** Standard — documentation; no code, no guard, no ADR decision.
- **Scope:** `docs/review-findings.md` (Trace column, statuses checked against the code, D21–D33, RF- citation note, trace table of the earlier reviews); `docs/tech-debt.md` TD-25…TD-36.
- **Out of scope:** renaming register ids (cited as RF-… instead, so existing references stay valid); Nam's written decisions on production blockers (J4: waiting list item 3 of `HANDOFF.md`); `HANDOFF.md` — updated after the parallel session `plans/2026-11-11-kb-gap-procedure/` commits (Nam chose to run P2-7 in parallel, 2026-11-12, touching only the two documents and this folder).
- **Files:** `docs/review-findings.md`, `docs/tech-debt.md`, this folder.
- **Invariants and ADRs touched:** I9 (findings become rules, checks, KB or tech debt); cross-references only.
- **Stop points expected:** none (item 9: the other session's uncommitted files are not touched or staged).
- **Acceptance criteria:**
  1. Every row of the register has a non-empty Trace (an artefact, or the reason none is needed).
  2. D21–D33 of the KB `behaviours.md` are rows of the register.
  3. Every status in the register agrees with the code on 2026-11-12 (each "Addressed" names an existing rule, test, KB entry or ADR).
  4. Each of the 20 "no artefact" and 2 "partial" items of design review WS-1 §8, and each H4 item, is closed with its artefact or has a TD line with a deadline.
  5. Open roadmap items of the design review have a TD line with a deadline.
  6. Both suites green; only the planned files staged.
- **Tests:** none new (documents). Both suites before the commit.
- **Subagents planned:** `pls-x-reviewer`, `sonnet`, effort `medium` (Standard), one round.
- **Documents to update in the same commit:** the two documents; `HANDOFF.md` follows in a separate commit (see Out of scope).
