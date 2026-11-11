# REQ-003 — Record the escalation date-time

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「エスカレーションした日時を記録し」)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 escalates an inquiry, the 問い合わせ site shall record the date and time of the escalation on that inquiry.

## Acceptance criteria

1. After the escalation, the inquiry shows an エスカレーション日時 (label `[assumed]`, Q12) holding the date and time of the escalation to the minute; through the API `get` it differs from the time of execution by less than 1 minute.
2. Before any escalation, the エスカレーション日時 of an inquiry is empty.
3. The escalation changes no other field of the inquiry: 状況 (`[assumed]`, Q6), 対応担当 (`[assumed]`, Q7), サポート責任者, 優先度, 対応期限 keep their values.
4. On a second escalation of the same inquiry, the recorded value follows Q8 (`[assumed]`: allowed; the latest date-time replaces the earlier one).
5. On the edit screen the エスカレーション日時 is read-only (`[assumed]`, Q12). *(Screen-only: the API can still write it — KB D17; an API test cannot show that users cannot change it.)*

## Notes for P2

- No existing column holds this: 受付日 and 対応期限 have other meanings, 更新日時 changes on every save, AI実行記録 is the AI stamp. A new column is therefore needed (checked against `config/inquiries/site.json` and `design/slot-ledger.json`, 2026-11-11). A new column → grid, filters and editor layout: Q12.
