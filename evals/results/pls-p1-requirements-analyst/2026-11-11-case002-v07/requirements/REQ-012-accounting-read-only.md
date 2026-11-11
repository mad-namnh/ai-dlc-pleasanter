# REQ-012 — 経理チーム cannot change inquiries or 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (経理の人は見るだけで、問い合わせの内容を変えたりはしません); impact on the existing process エスカレーション derived from REQ-010 (see notes)
- **Type (EARS):** unwanted behaviour

## Requirement

If a member of the 経理チーム tries to create, change or delete an inquiry or a 対応履歴 record, then the system shall refuse it.

## Acceptance criteria

1. As the 経理 test user: API create, update and delete on 問い合わせ and on 対応履歴 → refused (HTTP 403, 「この操作を行うための権限がありません。」, KB D19); the records are unchanged.
2. As the 経理 test user: the edit screen shows no save or delete button (KB D19).
3. As the 経理 test user: executing the process エスカレーション on a 優先度 高 inquiry in 状況 対応中 through the API → refused (403); 状況 and エスカレーション日時 unchanged, no mail sent.
4. As the 経理 test user: adding a comment → refused (403, KB D19).
5. Whether the エスカレーション button is shown to 経理 at all follows Q16 (`[assumed]`: not shown).
6. Support staff (non-経理) can still escalate as before (REQ-001/REQ-002 tests T-001…T-004 still pass).

## Notes

- **Derived impact on an existing element:** the process エスカレーション has no access control. KB D19/D20: a read-only user still sees a process button whose display condition matches, and pressing it is refused. So 経理 would see エスカレーション on 優先度 高 inquiries. Hiding it needs process access control, which then must list everyone who may escalate — this touches G1-approved Q1 (anyone with edit rights). Hence asked as Q16, not decided here.
- Export rights for 経理 are not requested — Q17 `[assumed]` none.
