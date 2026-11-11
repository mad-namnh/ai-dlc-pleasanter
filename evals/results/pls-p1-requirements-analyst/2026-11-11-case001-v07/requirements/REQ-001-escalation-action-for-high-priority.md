# REQ-001 — One-click escalation of a high-priority inquiry

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「優先度が「高」の問い合わせは、対応担当がワンクリックでサポート責任者にエスカレーションできるようにしたい。」)
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 優先度 is 「高」 and its 状況 is 受付, 対応中 or 顧客回答待ち `[assumed]` (Q3), the system shall offer the 対応担当 `[assumed]` (Q1) a エスカレーション action that escalates the inquiry to its サポート責任者 in one click.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 「高」 and 状況 対応中, a エスカレーション button is shown; pressing it once escalates the inquiry with no further input `[assumed]` (Q11).
2. Executing the エスカレーション action through the API on such an inquiry succeeds (HTTP 200) and the effects of REQ-003 and REQ-004 follow.
3. `[assumed]` (Q3) On an inquiry with 優先度 「高」 and 状況 解決 or クローズ（対応不要）, the button is not shown and execution through the API is refused; the record is unchanged.
4. `[assumed]` (Q4) On an inquiry that has already been escalated (エスカレーション日時 set), the button is not shown and execution through the API is refused; the recorded date-time is unchanged.
5. `[assumed]` (Q1) A user who can edit inquiries sees and can execute the action; a user with read-only permission cannot execute it (refused, record unchanged).
6. *(Partly not automatically testable: whether the button is rendered is checked on the edit screen by a person on dev; the API criteria 2–5 are automatic.)*

## Notes for P2

- 優先度 is `ClassE` (choices 高/中/低); 対応担当 is `Owner`; サポート責任者 is `Manager`.
- Q1: if only the inquiry's own 対応担当 (the person in `Owner` of that record) may escalate, the KB only documents access control by group / user / dept lists (D20), not by a record's own `Owner` — unverified, P2 must verify before designing.
- Read-only users still see process buttons whose display condition matches (D19); hiding needs access control (D20).
