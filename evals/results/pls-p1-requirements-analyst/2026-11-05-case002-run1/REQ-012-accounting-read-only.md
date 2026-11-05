# REQ-012 — 経理チーム cannot change inquiries or 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 2 (「経理の人は見るだけで、問い合わせの内容を変えたりはしません」)
- **Type (EARS):** unwanted behaviour

## Requirement

If a member of the 経理チーム attempts to create, update or delete an inquiry or a 対応履歴 record, then the system shall refuse the change.

## Acceptance criteria

1. API `create`, `update` and `delete` by the 経理 test user on the 問い合わせ管理 site → HTTP 403 「この操作を行うための権限がありません。」; the record is unchanged (KB D19).
2. The same three operations on the 対応履歴 site → HTTP 403; nothing is created or changed.
3. Adding a comment by the 経理 test user → HTTP 403 (KB D19) (`[assumed]` no comments needed, Q15).
4. On the edit screen of an inquiry and of a 対応履歴 record, the 経理 test user sees no save or delete button (KB D19).
5. Changing a record from the AI first response (AIで一次対応する) is not possible for the 経理 test user (the save is refused, criterion 1).
