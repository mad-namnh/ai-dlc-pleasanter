# REQ-011 — 経理チーム can view the 対応履歴 of 請求 inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 2 (「対応履歴も見られると助かるそうです」)
- **Type (EARS):** state-driven

## Requirement

While a user is a member of the 経理チーム, the system shall let that user list and open the 対応履歴 records linked to inquiries whose カテゴリ is 請求.

## Acceptance criteria

1. A test user in the 経理 group can open the 対応履歴 list and, filtering 問い合わせ on a 請求 inquiry, sees all its 対応履歴 records (count equal to the administrator's).
2. The same user can open a 対応履歴 record of a 請求 inquiry (API `get` → HTTP 200) and sees 対応日時, 対応種別, 作業時間 and 対応内容.
3. *(対応履歴 of inquiries in other categories: same open point as REQ-010 — `[assumed]` visible, Q13; restriction → EP-5.)*

## Notes (for P2)

- The 対応履歴 site (`responses`) is not a managed site yet (EP-1). Whether it inherits permissions from 問い合わせ管理 is unknown (EP-3); KB D19 covers read access on child sites that inherit permissions only.
