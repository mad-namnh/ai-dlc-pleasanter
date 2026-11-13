# Plan — P3-3 refusal messages with the next action; no traceback to the person (design review C5, WS3-F11)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent = the P3-2 commit
- **Objective:** every refusal the review named tells the person what to do next, and an unexpected error ends in one readable line (no Python traceback) unless the operator asks for the trace.
- **Tier:** Standard — messages and the top-level error handler; no guard condition changes (each refusal still refuses in the same cases, with the same exit code).
- **State found (2026-11-12):** malformed files → `BadFile` refusals (P2-1); timeouts → `uncertain` with next action (P1-1); partial write → recovery states with `apply_outcome_message` (P1-1). Still open:
  1. any exception other than `Fail` that escapes `main` prints a traceback (`pls.py` `__main__`);
  2. "`<R>` has status X, not 'planned'" (apply, package) — no next action;
  3. "`<s>` → site N is not a site this release may write in E (stale plan, or a shared site)" — no next action;
  4. `pls_side_effects.apply_refusal`: a string where a list of mail items is expected is printed character by character.
- **Change:**
  1. `__main__`: `Fail` as before; any other `Exception` → `pls: unexpected error (<Type>: <first line>) — a defect in pls, not a refusal; nothing after this point ran. Run again with PLS_DEBUG=1 to see the trace and report it.` exit 3; with `PLS_DEBUG=1` the traceback is printed too. The run log already records the message (`pls_log.run`).
  2. One helper `not_planned_message(release, status)` used by apply and package: open states → `pls mark-applied` with exports (read back first); `rolled-back` / `applied` / `refused` → new release plan with a new id.
  3. Stale-plan refusal adds: "check envs.<env>.sites, then make a new release plan (pls release-plan with a new id)".
  4. `apply_refusal`: a string value is one item.
- **Acceptance criteria:**
  1. An unexpected exception prints no `Traceback` line without `PLS_DEBUG`, prints it with `PLS_DEBUG=1`, exit 3.
  2. Each of the three messages names a next action (a `pls` command); tests assert it.
  3. A string mail-change value is printed whole.
  4. Tests fail on the parent; both suites green (3.10 too).
  5. `docs/architecture.md` exit codes / `docs/setup.md` mention exit 3 and `PLS_DEBUG` if they list exit codes; TD-36, HANDOFF updated.
- **Subagents:** `pls-x-reviewer` sonnet/medium.
