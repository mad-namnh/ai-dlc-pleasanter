# Plan — TD-30: skills sync/check, launcher message, unpack over uncommitted edits

- **Date / branch:** 2026-11-13 / `brownfield-adr`; parent `6b1e889`
- **Task (Nam, 2026-11-13):** "review xong thì commit rồi làm tiếp TD-30" — `docs/tech-debt.md` TD-30 = `docs/reviews/architect-review-d3.md` N1, N2, N4.
- **Tier:** Standard (tool UX; no write guard, gate or Pleasanter write). Review `pls-x-reviewer`, `sonnet`, medium.
- **Already done before this task:** N1 "every difference is reported as newer" — `_version_direction` (newer / older / same version).

## Change
- **N1 orphans:** `skills check` reports a skill in the lock that the framework no longer has, and a folder in `.claude/skills` that is neither in the lock nor in the framework; `skills sync` removes the first kind only (pls installed it) and leaves the second alone.
- **N1 launcher:** `skills check` reports a project `pls.py` that differs from the framework's launcher (or is missing); `skills sync` writes it.
- **N1 template:** project files from `templates/project` belong to the project after `pls init` (profile, environments), so they are never copied over. The lock records a hash per template file; `skills check` names template files changed or added in the framework since the last sync; `skills sync` names them too ("merge by hand"), then records the new hashes.
- **N2:** the launcher exits with a clear message (not a traceback) when `.claude/framework.lock` is missing, unreadable or has no `path`, and `PLS_HOME` is unset.
- **N4:** `pls unpack` refuses when `config/<site>` has uncommitted changes (tracked or untracked), like `harvest`; outside a git repository it says so and goes on. `adopt`'s own remap of sites it has just created calls the unpack function directly, not the refusing command.

## Acceptance criteria
1. Orphan from the lock: reported by check, removed by sync, gone from the lock; a foreign folder: reported, never removed.
2. Launcher: a changed or missing `pls.py` is reported and rewritten by sync; after sync check is clean.
3. Template: a changed or new framework template file is reported by check and by sync, and is never written into the project; after sync, check is clean.
4. Launcher with no lock and no `PLS_HOME`: exit code non-zero, a message naming `framework.lock` and `PLS_HOME`, no traceback.
5. Unpack: tracked edit or untracked file under `config/<site>` → refused, files unchanged; clean tree → unpacks; no git repository → unpacks with a note; `adopt` still remaps new sites.
6. New tests fail on the parent; suites green (3.12, 3.10, node).
7. Docs: TD-30 closed; architecture `pls init` / `skills` row and `unpack` row; setup.md if it describes sync; `HANDOFF.md`.
