# Plan — P3-2 no application names or customer-side site ids in the core (design review A5)

- **Date / branch / parent commit:** 2026-11-12 / `brownfield-adr` / `a19fe9a`
- **Objective:** the core (`tools/pls` without tests, `skills/`, `templates/`) names no brownfield application and cites no adopted site id as evidence; the display grouping of POSSIBLE numbers recognises log calls by a generic rule instead of one app's logger names.
- **Tier:** Standard — display-only heuristic, comments, help text, KB wording; no guard, no write path.
- **Scope:**
  - `tools/pls/pls_scripts.py` `POSSIBLE_GROUPS` "log or message text": any call whose name contains `log`, `warn` or `error`, `console.*`, and a string that starts with a bracketed tag (`'[orders] …'`); the app-specific names go.
  - Comments / docstrings in `pls_scripts.py`, `pls.py` (secret false alarm), help example of `pls test --var`, `canonical-defaults.json` evidence: no app name, no adopted site id (evidence by slice or probe id).
  - KB (`pls-kb-curator`): D21 text, `api.md` site package headings, probe D21 title — "an adopted brownfield site / app" instead of its id or name. BR3 probe site ids stay (probe ids are allowed, roadmap P3-2).
  - Tests: `test_scripts.py`, `test_adopt.py` lines that quote the app's name or logger names are reworded to neutral names.
- **Out of scope:** example ids that are MADLAB dev demo ids, not a brownfield app (`config-layout.md` `Group,372`); numeric fixtures in tests (`797` is just a number there); Nam's classification of the app as customer-owned (not needed: it goes from the core either way).
- **Acceptance criteria:**
  1. `grep -rniE "play ?board|pbWarn|pbLog|\[playboard\]|site 797|44656|42410|42411|44565" tools skills templates` → 0 hits outside `tools/pls/tests`, and 0 app-name hits in tests.
  2. A log call with a project-specific name or a bracketed tag (`notify('[orders] …')`, `appWarn(…)`) is grouped "log or message text"; a new test shows it and fails on the parent.
  3. Existing grouping tests still pass unchanged in meaning.
  4. KB version bumped in `skills/README.md`; `docs/tech-debt.md` TD-36 and `HANDOFF.md` say P3-2 is done.
  5. Both suites green; only planned files staged.
- **Tests:** new `test_possible_group_log_calls_without_app_names`; parent check in `../_agent-scratch/`.
- **Subagents planned:** `pls-kb-curator` (KB wording, haiku/low is enough — Light edits from supplied text); `pls-x-reviewer` sonnet/medium.
