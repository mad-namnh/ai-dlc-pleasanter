# Proposed ADR text — Role tests becomes a recorded profile field (needs Nam's approval of this exact text — stop point 1)

Direction chosen by Nam (2026-11-15): "Thành field có record".

**ADR-0020, Decision — paragraph "Profile records (guard inputs outside the four gates)", first sentence becomes:**

> The profile rows **Approvers**, **Operators**, **Origin**, **Role tests** and the `role` of an environment are set only through `pls profile set`, which records the person's words under `gates/profile/` and then writes the file; once a field has a record, the recorded value is the one `pls` reads, and lint L-PRF-01 reports a row that differs from its record or has none, and a stg / prod role without a record (`tools/pls/pls_profile_records.py`, roadmap P0-4). **Role tests** (`deferred` / `per-role keys`) is recorded because deferring role tests lowers what G3 proves. `pls init --approver` records the values the person typed on the command line (Role tests from `--stage`).

**ADR-0014, TB-1 row (Decision table), "profile rows Approvers / Operators / Origin read from their `pls profile set` record" becomes "profile rows Approvers / Operators / Origin / Role tests read from …".**

## Version 2 (after review R2; Nam chose "Sửa câu chữ ADR", 2026-11-15)

- ADR-0020: after "…lowers what G3 proves." add: "For Role tests no pls command reads the row (the skills do): its record gives tamper evidence — L-PRF-01 reports an unrecorded, unknown or differing row — not enforcement."
- ADR-0014 TB-1: unchanged (Role tests not listed under what pls enforces).
