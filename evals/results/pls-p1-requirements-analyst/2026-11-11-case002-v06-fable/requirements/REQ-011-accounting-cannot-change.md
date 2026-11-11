# REQ-011 — 経理チーム cannot change inquiries or 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 2: 「経理の人は見るだけで、問い合わせの内容を変えたりはしません」)
- **Type (EARS):** unwanted behaviour

## Requirement

If a member of 経理チーム attempts to create, change or delete an inquiry or a 対応履歴 record, then the system shall refuse the operation.

## Acceptance criteria

1. With a test user who belongs only to 経理チーム: API create, update and delete on the 問い合わせ site are refused (HTTP 403) and the record is unchanged.
2. The same on the 対応履歴 site (applies when REQ-012 is in scope).
3. The same user executing エスカレーション on an inquiry that meets its conditions (優先度 = 高, 状況 受付 / 対応中 / 顧客回答待ち) is refused (HTTP 403); 状況 and エスカレーション日時 are unchanged, and no escalation mail is sent. *(Mail part not automatically testable.)*
4. The same user cannot add a comment to an inquiry `[assumed]` (Q15).
5. The edit screen shows no save or delete button to that user. *(Checked by a person on the screen.)*

## Notes

- For P2: KB D19 (1.5.2) — with Read permission, create / update / delete / process execution / comments return 403, **but the エスカレーション button is still shown** to a read-only user when its display condition matches; pressing it is refused. Hiding it needs process access control (D20). Whether the button must be hidden is Q15; the assumed default is that refusal is enough, so no requirement asks for hiding it.
- `EditorReadOnly` and `ValidateRequired` are screen settings only (D17, D27); the refusal here must come from permissions, not from screen settings.
