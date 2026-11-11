# ADR-0021: Machine setup profile, key files and environment overrides

- **Status:** Proposed (2026-11-11) — describes what `pls` does today; Nam accepts, changes or rejects it
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** I3, I7; ADR-0008 (connections, write guard), ADR-0013 (run-log actor), ADR-0014 (TB-1, TB-2, TB-9, TB-10, TB-11); `docs/setup.md`; design review 2026-11-09 A2 items 4–6; roadmap P2-6, P3-7

## Context

ADR-0008 says connections are local (`.pls/connections.json`, gitignored), keys are referenced as `env:NAME` or `file:NAME` "under `.pls/`", and writing needs the operator's opt-in `allow_write: true`. Since then `pls setup` and `pls init` were built (plan D4, 2026-11-05) so that a person starts a project with two commands. That flow stores a key outside the project, writes `allow_write: true` without asking, and labels the environment `dev`. Three environment variables also change which files `pls` reads. The design review of 2026-11-09 (A2 items 4–6) found these decisions in code with no ADR, and the first one in conflict with ADR-0008's wording. ADR-0014 records the trust each of them needs (TB-9, TB-10, TB-11) but not the decision itself.

## As built (2026-11-11, `pls` on `brownfield-adr`)

**`pls setup [--profile NAME]`** (once per machine and Pleasanter environment; default name `dev`; `tools/pls/pls.py` `setup_profile`):
- asks for the URL, the folder (URL or id), the API key (hidden input) and the login id; checks with the key that the folder is readable and finds the user id;
- writes `<profile dir>/<name>.json` (URL, folder id, login, user id, `principals.admin = User,<id>`, `keys.admin = file:<absolute path of the key file>`, `default_key: admin`, **`allow_write: true`**) and the key alone in `<profile dir>/<name>.admin.key` (mode 600 where the file system supports it);
- profile dir: `~/.pls/profiles/`, or the folder named by `PLS_PROFILE_DIR` (`profile_dir`).

**`pls init <dir> [--profile NAME]`** (`pls.py` `_main`, `apply_profile`): uses the named profile, or `dev` when `dev.json` exists; writes into the new project `environments.json` → `envs.dev` with **`role: dev`**, the folder id and `principals`, and `.pls/connections.json` → `dev` with the URL, the key reference and `allow_write` from the profile (true). Without a profile the person fills both files by hand (`docs/setup.md`).

**Key references** (`tools/pls/pls_http.py` `resolve_key`): `env:NAME` reads an environment variable; `file:PATH` reads a file, relative to the folder of the connection file — an **absolute path is used as it is** (the profile flow writes one under `~/.pls/profiles/`). A literal key is refused. Key values are never printed or logged.

**Environment overrides:**

| Variable | Effect | Code |
|---|---|---|
| `PLS_CONNECTIONS` | another connection file instead of `.pls/connections.json`; the same role and `allow_write` rules apply to it. `pls test-users` refuses when it names a file outside the project's `.pls/` (test users' secrets stay there) | `pls_http.py` `connections_file`; `pls.py` test-users |
| `PLS_PROFILE_DIR` | another folder for machine profiles | `pls.py` `profile_dir` |
| `PLS_ACTOR` | the run-log actor (else git `user.name`, else the OS user); self-asserted, not an identity check | `tools/pls/pls_log.py` `actor` |
| `PLS_HOME` | the framework checkout the project launcher runs (ADR-0022) | project `pls.py` launcher |

What does not change with any of them: `role: prod` is never written; writes need `role` dev / stg from `environments.json` **and** `allow_write: true` in the connection used (`assert_writable`); stg needs G4 (ADR-0020).

## Open questions

- [ ] Should `pls setup` ask before opting in to writes, and default to `false` (roadmap P3-7)? — *Nam; P3-7 changes the code once decided*
- [ ] Should `file:` references be confined to `.pls/` and the profile folder (refuse other absolute paths), as ADR-0008's wording suggests? — *Nam*

## Options

### Option A — Keep as built; amend ADR-0008's wording ("a file under `.pls/`, or the key file of a machine profile")
- Pros: no code change; the two-command start keeps working; the key stays outside every repository.
- Cons: setup opts in to writes without a question (TB-10: a stg URL typed into setup becomes a writable `dev`); any absolute key path is accepted (TB-11).

### Option B — As built, but setup asks for the opt-in (default `false`) and states the role it will write; `file:` limited to `.pls/` and the profile folder
- Pros: closes the two "not covered" gaps of TB-10 and TB-11 in code; matches ADR-0008's operator opt-in.
- Cons: one more question at setup; projects whose connection names a key file elsewhere must move it.

### Option C — No machine profile: the person fills `.pls/connections.json` by hand for each project
- Pros: one rule, as ADR-0008 wrote it.
- Cons: drops a flow that is used and tested; more hand edits of the file that holds `allow_write`.

## Decision

**Proposed: option B**, the opt-in part through roadmap P3-7 and the `file:` limit as a separate item; option A describes the state until then. The environment overrides stay as listed above; each is an accepted boundary only through ADR-0014 TB-9.

## Consequences

- Easier: what `pls setup` / `init` may write, where keys live and what each variable changes is now in one place; ADR-0008's key rule and this ADR no longer contradict each other once ADR-0008 points here.
- Harder / costs: option B changes setup (a question, a refusal for key paths outside the two folders) and needs tests for both.
- Follow-up: P3-7 (opt-in default); a `tech-debt.md` line for the `file:` limit if accepted (P2-7); ADR-0008 and `docs/setup.md` point here once accepted.
