# ADR-0019: Test users in their role's group (supersedes ADR-0017 rules 2–3)

- **Status:** Accepted (2026-11-11) — option B, decided by Nam after the probe; built 2026-11-11 with ADR-0018 option C (`pls test-users`)
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Supersedes (once accepted, depending on the option):** ADR-0017 rule 3 (members of a created group) with A or B; with B also the sentence of rule 2 "Never update or delete an existing group", which becomes "Never delete an existing group; update one only to add a test user (option B)". The rest of ADR-0017 stays as it is.
- **Related:** ADR-0018 (test users and keys, option C), ADR-0017 (groups from the permission design), ADR-0006 (logical principals), ADR-0014 (TB-14 shared tenant resources, TB-15 API key privilege); `docs/plan.md` Step 4d AU5

## Context

ADR-0018 (Accepted, option C) has `pls` create one test user per role on dev and issue its key. A role test proves the role's rights only if the test user gets them the way a real member does: for `principal: "Group"`, by being a **member of the role's group** bound by `pls principals`. ADR-0017 does not allow that:
- rule 3: a group that `pls` creates gets one member, the operator;
- rule 2: `pls` never updates an existing group. The three groups of the trial `pls-demo-contracts` already exist (created 2026-11-11), so their test users could only join through an update.

What is known:
- Observed (KB `api.md` "Users and groups"): `/api/groups/create` with `GroupMembers: ["User,<id>,False"]` makes that user a member; users and groups are tenant-wide (TB-14).
- Manual, not observed: `POST /api/groups/{id}/update` (tenant manager; `GroupName`, `Body`, `GroupMembers`, `GroupChildren`). `GroupMembers` must list **all** members, the new ones and the unchanged ones — so the array replaces the member list. What an omitted field does is not described. https://pleasanter.org/en/manual/developers-guide/api/group-operations/api-group-update/
- Not known: whether `/api/groups/get` returns the members at all. Without that, `pls` cannot add a member to an existing group without risking the removal of others.

Constraints:
- A group on dev may hold real people added by a person (ADR-0017: "other members are people data"). Removing one by accident changes what that person can see on dev, and on the MADLAB demo server also on stg (one tenant).
- A read-then-replace update can race with a person editing the same group in the UI. What Pleasanter does then is not observed (whether a group carries `UpdatedTime` / `Ver` and whether an update honours them is an open question); `docs/review-criteria.md` C9 expects such a check before a write.
- On the MADLAB demo server dev and stg are one tenant: a test user added to a group there also gets that group's rights on stg sites (A and B alike). On real projects dev and stg are different tenants (ADR-0017).
- Test users are created only by `pls` on dev (ADR-0018), with the fixed prefix `zz_test_`; stg and prod are out of scope.

## Open questions

Answered by the probe `plans/2026-11-11-test-users-in-groups/probe-group-members.py` (operator, MADLAB dev 1.5.2, 2026-11-11 19:42; KB `api.md` "Users and groups", group-members probe rows):
- [x] Does `/api/groups/get` return a group's members? **Yes**: `GroupMembers`, an array of `"User,<id>,<True|False>"`; `GroupChildren` an array.
- [x] Does `/api/groups/{id}/update` with `GroupMembers` replace the member list? **Yes**: a member left out was removed.
- [x] Does an update without `GroupMembers` (only `Body`) keep the members and `GroupName`? **Yes, both.**
- [x] When a member user is deleted, does the group's member list drop it? **Yes** (API read `[]`; the UI showed no user).
- [x] Is the group-administrator flag kept by an update and shown by the read? **Yes.** B still keeps every member's flag as read.
- [x] Does an update that leaves out `GroupName` or `Body` clear them? **No**, both are kept. B still sends both exactly as read.
- [x] Does a group record show `UpdatedTime` / `Ver`? **Yes**, both fields are present. Whether an update honours them is **not** observed: B re-reads them just before the write and refuses on a change, which narrows the race but does not close it.

Not answered by the probe:
- [ ] `GroupChildren` on update (left out by `pls` in every option; a group with child groups is refused in B).
- [ ] Departments as members (`Dept,<id>`): kept as read, never added.

## Options

Common rules: dev only, not a sandbox, `assert_writable`, typed confirmation listing every change, never stg or prod; the only member `pls` ever adds is a `zz_test_` user it created for that role (ADR-0018), never as group administrator; `pls` never deletes a group, never removes a member, never changes a member's administrator flag, never renames a group, and never changes `Body` or child groups of an existing group; run-log metric of its own for the changes (`group_members_added`); write-path inventory (`test_write_guards.py`).

### Option A — Test users join only when `pls` creates the group
Rule 3 becomes: members are the operator **and** the role's test user. Rule 2 stays: an existing group is never updated; `pls` prints the exact test user to add in the UI for each existing group, and role tests for that role stay `deferred` until the person has done it (`pls` checks membership if the API shows it).
- Pros: no update of an existing group; no risk to other members.
- Cons: a person step for every group that already exists — on the trial, all three groups; on a project whose groups were created before its test users, every group.

### Option B — A, and `pls` adds the test user to an existing group by read, add, write, check
Rule 2 becomes: `pls` may update an existing group on dev only to **add** its own test user. Allowed only when the read shows the full member list in a known format and no child groups; `pls` sends the read list (each member with its flag as read) plus the test user, and `GroupName` and `Body` exactly as read; if the record has `UpdatedTime` / `Ver`, it re-reads just before the write and refuses on a change. It then reads back and requires every earlier member with the same flag, and the test user, to be present. Any difference is a refusal that prints the earlier list (ids only) so a person can restore it; no retry, no automatic repair.
- Pros: no person step on dev — the AU5 "done when".
- Cons: depends on the probe's answers; a person's change in the UI between the read and the write is lost (the read-back shows it, nothing more); one more write path to a tenant-wide object.

### Option C — Recreate the group
Delete and recreate the group with the new members.
- Rejected: changes the group id that `environments.json` binds, drops every member, and ADR-0017 forbids `pls` to delete groups.

## Decision

**Option B** (Nam, 2026-11-11), after the probe showed the members readable and the update replacing the list. ADR-0017 rule 3 and the sentence of rule 2 named in the header are superseded; A remains what happens wherever B refuses (the person adds the test user in the UI, and that role's tests stay `deferred`).

## Consequences

- What becomes easier: role tests run on dev with no person step (with B), including projects whose groups already exist.
- What becomes harder / costs: TB-14 gains a tool update of a tenant-wide object (B); the read-write race is detected, not prevented.
- The probe script is a one-off outside `pls`: not in the write-path inventory, no run-log line; kept in the plan folder as the record of the KB entry.
- Follow-up work: KB entry from the probe (`pls-kb-curator`); ADR-0017 status line "rules 2–3 superseded by ADR-0019" once accepted; build together with ADR-0018 C; ADR-0014 TB-14 row; P4 skill text.
