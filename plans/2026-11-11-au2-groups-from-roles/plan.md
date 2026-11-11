# Plan — AU2: groups from `design/roles.json`

- **Task (Nam, 2026-11-11):** "lam tiep AU2" — docs/plan.md Step 4d AU2: after G2, `pls principals --env dev --create` creates the missing groups and binds them.
- **Tier:** Critical (new write path to Pleasanter, tenant-level object shared by dev and sandboxes — ADR-0014 TB-14/TB-15; needs a tenant-administrator key).
- **Status:** Nam chose "ADR first + probe" (2026-11-11). Written: ADR-0017 (Proposed) and the probe script; review accept with fixes, fixed (`review.md`). Waiting: the operator runs the probe on dev; then Nam decides on ADR-0017. Code is built only after that.

## Facts
- Current `bind_principals` (`tools/pls/pls.py`) only looks groups up by name (`/api/groups/get`) and reports the missing ones for a person to create.
- KB (`skills/pls-kb-pleasanter/references/api.md`) has no entry for group creation: unknown on 1.5.x by observation.
- Pleasanter manual (not observed): `POST /api/groups/create` (1.2.24+; `GroupMembers` 1.3.4+), body `GroupName`, `Body`, `GroupMembers`, `GroupChildren`; **tenant administrator only**. https://pleasanter.org/en/manual/api-group-create
- `kb-verify` probes are confined to a probe site (`pls_kbverify.py` FORBIDDEN_KEYS): it cannot create a group as is.

## Open questions (Pleasanter, to be probed on dev)
1. Does `/api/groups/create` on dev 1.5.x create a group with the operator's key? Response shape (new GroupId?)
2. ~~Is the operator's dev key a tenant administrator?~~ Yes (Nam, 2026-11-11).
3. Can a group created by API be deleted by API (`/api/groups/{id}/delete`) — needed to clean up a probe.
