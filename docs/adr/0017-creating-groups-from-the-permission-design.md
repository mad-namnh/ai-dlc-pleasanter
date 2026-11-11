# ADR-0017: Creating the groups of the permission design on dev (`pls principals --create`)

- **Status:** Accepted (2026-11-11) — Option B, decided by Nam after the probe; built the same day (`pls principals --create`)
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** ADR-0006 (site permissions in git, logical principals), ADR-0008 (HTTP transport, `assert_writable`), ADR-0014 (TB-14 shared tenant resources, TB-15 API key privilege), ADR-0009 (KB verification); `docs/plan.md` Step 4d AU2

## Context

P2 writes `design/roles.json` (role → `group_name`). After G2 a person creates those groups in the Pleasanter UI, then `pls principals --env dev` binds their ids by name into `environments.json`. In the trial `pls-demo-contracts` this was the only person step between G2 and P3 that is not a decision: the names are fixed by the design, and a typo in the UI breaks the binding. AU2 asks `pls` to create the missing groups itself.

Constraints:
- Groups are **tenant-wide**: dev and every sandbox share them (TB-14). A group created for one project is visible to every site of the tenant.
- The Pleasanter manual (not yet observed by us) says `POST /api/groups/create` (1.2.24+), `/api/groups/{id}/update` and `/api/groups/{id}/delete` can be called **only by a tenant administrator**. The operator's dev key is a tenant administrator (Nam, 2026-11-11) — the same key `pls` already uses (TB-15).
- `pls kb-verify` probes are confined to a probe site and cannot create a group (`pls_kbverify.py` FORBIDDEN_KEYS).

## Open questions

- [x] Does `/api/groups/create` on our dev create a group without members, and what does it answer? **Yes**: HTTP 200, `{Id, StatusCode, Message}`, and `Id` is the new GroupId (probe 2026-11-11, MADLAB dev 1.5.2, tenant-administrator key; KB `api.md` "Users and groups").
- [x] Does the server refuse a second group with the same name? **No**: a second create with the same name made a second group. `pls` alone prevents duplicates (rule 2: look up every match first; refuse an ambiguous name).
- [x] Can the API delete a group it created? **Yes**: `/api/groups/{id}/delete` → HTTP 200; nothing left (same probe). `pls` itself does not delete groups.
- [x] Do dev and stg share one tenant? **On the MADLAB demo server yes, on purpose** (demo, one tenant only); in real projects dev and stg are different tenants (Nam, 2026-11-11). Rule 1 therefore holds on real servers; on the demo server a group created on dev is also visible to stg, which Nam accepts for the demo.
- [x] Should created groups get members? **The operator** (`envs.<env>.principals.admin`), so the person can test at once (Nam, 2026-11-11). Other members are people data, added by the person.
- [ ] Limits of the lookup, not observed: whether the `GroupName` filter is exact, partial or case-insensitive. `pls` compares names exactly (case-sensitive) and treats an answer of more than one page as unknown (refused). A group whose name differs only by case is not seen as the same group. A role already bound is not checked again for duplicates.
- [ ] `GroupMembers` on create is not observed on 1.5.2 (manual: 1.3.4+, `"User,<id>,False"`). `pls` asks the person to check the membership of the first created group once; the result goes into the KB.

## Options

### Option A — Person step (as now)
- Pros: no new write path; no tenant-level change by a tool.
- Cons: a manual step after every G2 on dev; names typed by hand.

### Option B — `pls principals --env dev --create`: create the missing groups, then bind
Rules:
1. Only for an environment with `role: "dev"` and `allow_write: true` (`assert_writable`) — never stg (stg groups are the customer's), never prod, never a sandbox name (sandboxes share the base tenant; the base env creates).
2. Only names from `design/roles.json` with `principal: "Group"` and a final `group_name` (no placeholder, no surrounding spaces) — any other role to create is refused before the confirmation; only when a lookup by exact name finds **no** group. Two or more groups with the name → refuse, nothing created. Today's binding (`_lookup` in `tools/pls/pls.py`) does **not** do this: it returns nothing when a name matches more than one group, and `bind_principals` then reports the role as missing — `--create` needs a lookup that returns every match, and binding should refuse an ambiguous name too. Never update or delete an existing group.
3. One member, the operator (`envs.<env>.principals.admin`, `User,<id>`, not a group administrator); no child groups; `Body` names the role only. Refused when the operator is not bound.
4. One typed confirmation at a terminal listing every name to be created (same rule as other writes: an agent never adds `--yes` unless the person asks).
5. Run-log event lists the created group ids in a metric of their own, `groups_created` (`metrics.written` stays site ids, `tools/pls/pls_log.py`); the command joins the write-path inventory test (`test_write_guards.py`).
6. After create, read back by name; a missing or doubled group is a refusal with the ids found (no retry).
- Pros: removes the person step; names come from the design only; same guards as other dev writes.
- Cons: a tool now changes a tenant-wide object; the key must stay a tenant administrator (TB-15 cannot be narrowed for this command).

### Option C — Generate a checklist only
`pls principals` prints the exact names and a copy-paste list for the UI.
- Pros: no write. Cons: the step stays manual (this is mostly what `pls principals` already prints).

## Decision

**Option B** (Nam, 2026-11-11) — the probe confirmed create, delete and that duplicates are not refused by the server (rule 2 covers them). Option A stays the way on stg, prod and wherever `--create` is refused.

Built (2026-11-11): `bind_principals` in `tools/pls/pls.py` (exact-name lookup of every match; an ambiguous name or a failed lookup is refused, also when only binding), `Client.create_group` in `pls_http.py`, `principals` is a writing command in the run log and the write-path inventory (`test_write_guards.py`); tests `tools/pls/tests/test_principals_create_groups_on_dev_only.py`.

## Consequences

- What becomes easier: P3 on dev starts right after G2 without a UI step (AU2 "done when": the three groups of the trial exist on dev without a UI step).
- What becomes harder / costs: TB-14 gains a tool write to a tenant-level object; TB-15's follow-up (least-privilege key) cannot cover this command on dev.
- The probe script (`plans/2026-11-11-au2-groups-from-roles/probe-group-create.py`) is a one-off outside `pls`: it is not in the write-path inventory (`test_write_guards.py`) and leaves no run-log line. It stays in the plan folder as the record of the KB entry (KB `api.md` "Users and groups") and is not run again; a new probe of groups is a new script with its own review.
- Follow-up work: KB entry from the probe (via `pls-kb-curator`); `bind_principals` + `--create`; tests (dev only, stg and sandboxes refused, existing group never touched, ambiguous name refused and not created, confirmation, run-log ids); P2 skill text ("created by `pls principals --create` after G2") and lifecycle gates text; ADR-0014 TB-14 row.
