# REQ-012 — 経理チーム cannot change inquiries or 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (経理の人は見るだけで、問い合わせの内容を変えたりはしません)
- **Type (EARS):** unwanted behaviour

## Requirement

If a member of the 経理チーム tries to create, change or delete an inquiry or a 対応履歴 record, then the system shall refuse the operation.

## Acceptance criteria

1. API create / update / delete by a 経理 test user on the 問い合わせ site → HTTP 403, record unchanged.
2. The same on the 対応履歴 site → HTTP 403, record unchanged.
3. Executing エスカレーション on a matching inquiry (優先度 高, 状況 対応中) as the 経理 user → HTTP 403, 状況 and エスカレーション日時 unchanged.
4. Adding a comment as the 経理 user is refused (403) `[assumed]` (Q15: 経理 does not comment).
5. The edit screen shows no save or delete button to the 経理 user.
6. The エスカレーション button may still be shown to the 経理 user on matching inquiries; pressing it is refused `[assumed]` (Q16; KB D19).
7. Export (CSV) is not available to the 経理 user `[assumed]` (Q15).

## Notes for P2

- KB D19 / D20: read-only users still see process buttons whose display condition matches; hiding them needs process access control (principal lists), which would also restrict who may escalate (open question Q1 of 2026-11-05). Not assumed here (Q16).
