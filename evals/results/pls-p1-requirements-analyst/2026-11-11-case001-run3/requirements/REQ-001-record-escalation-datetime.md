# REQ-001 — Record the escalation date-time

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「対応担当がワンクリックでサポート責任者にエスカレーション」「エスカレーションした日時を記録し」)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 executes エスカレーション on an inquiry whose 優先度 is 高, the system shall record the date and time of that escalation on the inquiry.

## Acceptance criteria

1. On an inquiry with 優先度 = 高 and 状況 = 対応中, executing エスカレーション with a single click (no other input) saves the inquiry, and the inquiry then holds an escalation date-time equal to the execution time (to the minute), readable through the API `get` and shown on the edit screen.
2. The escalation is directed to the user in the inquiry's existing 「サポート責任者」 field; no new field for the escalation target is added. `[assumed]` — Q1.
3. Executing エスカレーション does not change 状況, 優先度, 対応担当 or サポート責任者. `[assumed]` — Q6, Q7.
4. The escalation date-time cannot be edited by hand on the edit screen. `[assumed]` — Q12. *(Screen setting only: the API can still write it — KB D17. A test checks the screen setting, not API refusal.)*

## Notes for P2

- No existing column holds this value: 受付日 and 対応期限 are dates with other meanings, 更新日時 changes on every save, AI実行記録 belongs to the AI script. A new element is therefore needed (see impact in `index.md`).
- Who may execute it (only the record's 対応担当, or any support user) is open — Q2.
