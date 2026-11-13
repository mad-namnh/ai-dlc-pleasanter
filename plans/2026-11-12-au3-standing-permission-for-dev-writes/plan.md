# Plan — AU3 standing permission for dev writes (ADR-0024, accepted 2026-11-12)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent `e9daaa7`
- **Tier:** Critical — write confirmation (a control of every dev write). Main session Opus; review `pls-x-reviewer` on `opus`, effort high.
- **Nam's decisions (2026-11-12):** option B (until revoked); only `bootstrap` / `apply` / `migrate`; one record per sandbox.
- **Change:**
  1. `pls_profile_records`: field `dev-writes` (`on` / `off`) with `--env`; the environment must exist and have `role: dev` (and its role record, if any, `dev`); recorded like the other fields (approver of the profile, the person's quote, exclusive record file); `dev_writes(root, env)` returns the latest `on` record or None; a damaged record refuses (fail closed → typed confirmation).
  2. `pls.py`: `_confirm_write(r, cmd, env, release, yes, what)` — `--yes` → "--yes"; else for `apply` / `bootstrap` / `migrate` on `role: dev` with an `on` record → prints and returns `standing permission (<record>, <approver>)`; else the typed confirmation. `apply-log.json` `confirmed` records the mode; bootstrap / migrate print it.
  3. Lifecycle skill rule 3; `docs/setup.md`; `docs/architecture.md` §7.1 (`profile` row); ADR-0008 consequence noted in ADR-0024 only (ADR-0008 Proposed).
  4. Patches (protected paths, Nam applies): `CLAUDE.md` Mandatory 1 and `templates/project/CLAUDE.md` hard rule 3 name the exception.
- **Acceptance criteria:** 1. with an `on` record, apply / bootstrap / migrate on dev run without typing or `--yes`, and the release folder names the record; 2. stg, prod, a sandbox without its own record, an `off` (revoked) record, no record, a damaged record, a role record ≠ dev, and `principals --create` / `test-users` / `test` / `kb-verify` still need the typed confirmation; 3. recording refuses a non-dev environment and a non-approver; 4. tests fail on the parent; suites green (3.10); 5. docs and patches as above.
