# Review — ADR-0019 and probe-group-members.py (round 1)

- Reviewer: `pls-x-reviewer`, model opus, effort high; working tree against `20fe494`.
- Verdict: **accept with fixes**. No Critical or High.
- Reviewer ran: unit suite (404 OK), node (15 pass), 16 offline fake scenarios (no network), `git status` before and after (unchanged).
- Not verifiable by the reviewer: real 1.5.2 member field and format, update semantics, paging fields and `Offset`, soft delete, terminal behaviour on Windows, `UpdatedTime`/`Ver` on groups.

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | Member fields printed unfiltered; records could carry names or secret fields | Fixed: only ids and `User/Dept/Group,<id>[,flag]` strings printed; of records only keys, id fields and booleans |
| M2 | Medium | B depends on the group-administrator flag and on what an update does to omitted `GroupName`/`Body`; probe did not show them | Fixed: probe adds the test user with `True` and reports `GroupName` and `Body` on every read; ADR open questions added; B keeps flags and sends name and Body as read |
| L1 | Low | Paging that ignores `Offset` reads as "group vanished" | Fixed: a page with no new ids is an error |
| L2 | Low | Lost from precedents: unconfirmed / odd ids reporting | Fixed: `left_after_delete.unconfirmed`, `odd_ids`; ids not confirmed are never deleted |
| L3 | Low | Leftover check fragile (one exception hides the rest; missing paging fields → false "unknown") | Fixed: each check on its own; a group whose delete answered 200 and whose name finds nothing counts as gone |
| L4 | Low | Header vs option A; "never delete" not restated | Fixed: header conditional per option, replacement sentence for rule 2; common rules say never delete |
| L5 | Low | Race stated as fact; C9 not considered | Fixed: worded as not observed; open question on `UpdatedTime`/`Ver`; B re-reads before writing if present |
| L6 | Low | Demo server's shared stg tenant | Fixed: stated in Constraints |

Re-check after fixes (Orchestrator, reviewer's harness `h19/t1.py`, 15 scenarios): no leak (including member records with secret fields), no other group or user touched, every leftover reported. Fixes not re-reviewed independently.
