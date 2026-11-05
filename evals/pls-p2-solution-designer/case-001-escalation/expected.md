# Rubric — case 001

## Must

- [ ] Uses **standard settings + プロセス** (rung ≤ 2) for escalation: status change, date-time data change, display condition, mail notification. No new server script.
- [ ] Display condition expressed with **Status and 優先度**, not with a checkbox flag (D9). If a checkbox design was considered, it is listed as rejected with the reason.
- [ ] New status (or equivalent) added to the Status choices; new date-time column allocated in the slot ledger to a **free** slot (not ClassA–H, DateA–B, …), read-only.
- [ ] Impact analysis lists: view 未完了 (must include the new status), notification #1 (condition = view 2), aggregation by status, AI script status map, reminder 1 (condition 2).
- [ ] Notices that adding the new status to view 2 makes notification #1 fire on every escalation (second mail to [Manager]) and raises it back to P1/G1 instead of absorbing or ignoring it. *(Added 2026-11-05: escaped in slice #1, found by the independent run.)*
- [ ] Classification **config-only** with reason (nothing removed, no existing data changed).
- [ ] `traceability.json` maps every REQ to design elements and to config paths using stable keys (process `Name`, `ColumnName`, view `Id`).
- [ ] Open points carried over from G1 assumptions (who may escalate; mail delivery testability).

## Must not

- [ ] Edit `config/`.
- [ ] Hard-code SiteIds or rely on unverified Pleasanter behaviour without listing it as a probe/open point.
- [ ] Mark the design as approved.
