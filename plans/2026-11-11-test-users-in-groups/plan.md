# Plan — test users in their role's group (ADR superseding ADR-0017 rules 2–3)

- **Task (Nam, 2026-11-11):** "làm tiếp ADR thay rule 2–3 của ADR-0017" — follow-up of ADR-0018 (option C): test users must be members of their role's group.
- **Tier:** Critical (changes an Accepted ADR's rules; new write path that updates a tenant-wide group which may hold real people). Main session Opus 5.5.
- **Status:** ADR-0019 Proposed + probe; review; Nam runs the probe on dev; Nam decides. No `pls` code before that.

## Facts
- ADR-0017 rule 2: `pls` never updates or deletes an existing group; rule 3: a created group gets one member, the operator (`envs.<env>.principals.admin`, `User,<id>`).
- KB: group create with `GroupMembers` observed; `/api/groups/{id}/update` not verified; whether `/api/groups/get` returns members not recorded.
- Manual (not observed): `/api/groups/{id}/update` (tenant manager; `GroupName`, `Body`, `GroupMembers`, `GroupChildren`); `GroupMembers` must list **all** members, new and unchanged — i.e. the array replaces the list; omitted fields not described. https://pleasanter.org/en/manual/developers-guide/api/group-operations/api-group-update/
- ADR-0017: members other than the operator are people data, added by a person — an update that replaces the list could drop them.

## Probe questions
1. Does `/api/groups/get` return the members of a group (field, format)?
2. Does update with `GroupMembers` replace the list (a member left out is removed)?
3. Does an update without `GroupMembers` (only `Body`) keep the members, and does it keep `GroupName`?
4. When a member user is deleted, does it disappear from the group's members?

## Steps
1. ADR-0019 Proposed, README row.
2. `probe-group-members.py` (operator; dev only, not a sandbox, `assert_writable`, typed confirmation; probe user + probe group only; deletes both).
3. Review (`pls-x-reviewer`, opus/high); fix.
4. Nam runs the probe; KB via `pls-kb-curator`; Nam decides; then build ADR-0018 C with the chosen rule.
