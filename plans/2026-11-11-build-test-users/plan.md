# Plan — build ADR-0018 option C with ADR-0019 option B (`pls test-users`)

- **Task (Nam, 2026-11-11):** "làm tiếp build ADR-0018 C cùng ADR-0019 B".
- **Tier:** Critical (new write paths: users, group update, API key issue; test-user secrets; write guard inventory). Main session Opus 5.5.
- **Nam's decisions (2026-11-11):** `pls` adds `keys.<role>: file:test-users/<env>-<role>.key` to `.pls/connections.json` when the role has no key yet, refuses when it has a different one; the password file is kept; lifecycle (removal, rotation) → tech debt.

## Design
New subcommand `pls test-users --env <dev env> [--yes]` (module `tools/pls/pls_test_users.py`), a writing command.

Guards (before any request that writes): env `role: "dev"`, not a sandbox / connection alias, `assert_writable`; `design/roles.json` present; typed confirmation (env name) listing every write; `--yes` only on the person's instruction.

Per role of `design/roles.json` with `principal: "Group"`:
1. Must be bound (`envs.<env>.principals.<role>` = `Group,<id>`), role name `[a-z0-9_]+`; the group looked up by `group_name` must be exactly that id. Else refused (run `pls principals` first).
2. LoginId `zz_test_<project>_<role>` (project = folder name, lowercased, `[a-z0-9_]` only). Lookup: 0 → create; 1 → needs its password file on this machine, else refused; more → refused.
3. `connections.json` `keys.<role>`: absent → added after the key exists; equal → fine; different → refused before any write.
4. Group read: `GroupMembers` all `User|Dept,<id>,True|False`, `GroupChildren` empty, else refused. Test user already a member → nothing.

Writes, in order per role:
- **user:** password (random) written to `.pls/test-users/<env>-<role>.password` first; `POST /api/users/create`; read back by LoginId = the answered id. Metric `test_users_created`.
- **key** (no valid key file): only when the env's recorded Pleasanter version is covered by KB entry D32 (`verified_on`); login `/users/authenticate` (`Users_LoginId`, `Users_Password`, `ReturnUrl`), `/users/createapikey`, candidates from the answer and `/users/editapi` minus tokens seen before, each checked with `/api/users/get`; the accepted one → `.pls/test-users/<env>-<role>.key`. Not covered or failed → fallback B: the person issues the key (message names the files, never their content); exit 1.
- **connections:** add the key reference (only that key).
- **membership (ADR-0019 B):** re-read; `UpdatedTime`/`Ver` changed since the plan read → refused; update with `GroupName`, `Body` as read and `GroupMembers` = read list + `User,<uid>,False`; read back: every earlier member with its flag and the test user present, else refused with the earlier list. Metric `group_members_added`.
Nothing is printed of passwords, keys or cookies; files under `.pls/` get mode 600 where the OS allows.

## Files
- new `tools/pls/pls_test_users.py`; `tools/pls/pls_http.py` (`Client.create_user`, `Client.update_group`); `tools/pls/pls.py` (subcommand); `tools/pls/pls_log.py` (`WRITING`).
- tests: new `tools/pls/tests/test_test_users_on_dev_only.py`; `test_write_guards.py` (classify, inventory, `createapikey` as a write endpoint); `refusals_without_a_test.txt` only shorter.
- KB (curator): D32 in `behaviours.md` + `probes/index.json` (screen login and key issue, 1.5.2).
- docs: ADR-0018/0019 "built", ADR-0014 TB-14/TB-15, ADR-0008 consequence, `docs/architecture.md` if it lists commands, P4 skill (per-role keys at stage demo) + version, lifecycle skill if it names the step, `docs/tech-debt.md` TD-24 (lifecycle), TD-11/TD-13, `docs/plan.md` AU5, HANDOFF.

## Verify
Both suites (3.12, 3.10 since Python changes), new tests failing on parent `f9d6ddf` in a worktree under `../_agent-scratch/`; independent review (opus/high), max 2 rounds; trial on dev by Nam (`pls-demo-contracts`).
