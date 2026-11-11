# REQ-003 — Record the escalation date and time

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「エスカレーションした日時を記録し」)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 escalates an inquiry, the system shall record the date and time of the escalation on that inquiry in the item エスカレーション日時 `[assumed]` (Q9).

## Acceptance criteria

1. After the エスカレーション action is executed (API), reading the inquiry through the API returns エスカレーション日時 with date and time (at least to the minute) within one minute of the execution time.
2. The edit screen of the inquiry shows エスカレーション日時 with date and time.
3. Before any escalation, エスカレーション日時 of an inquiry is empty.
4. `[assumed]` (Q10) エスカレーション日時 cannot be changed by hand on the edit screen. *(Screen-only: the API can still write a column marked read-only — KB D17; not a data-integrity guarantee.)*
5. `[assumed]` (Q4) An inquiry is escalated at most once, so エスカレーション日時 holds the first and only escalation.
6. Other inquiries are not changed by the escalation.

## Notes for P2

- Overlap check (step 2): no existing column holds this. 受付日 (`DateA`), 対応期限 (`DateB`), 更新日時 (changes on every save), 対応回数 (`NumA`) and AI実行記録 (`ClassH`, AI stamp) all have another meaning. A new date-time item is needed; a free slot must come from `design/slot-ledger.json`.
- New column → grid, filters, editor layout, exports: where it is shown beyond the edit screen is Q9 (not a requirement until answered).
