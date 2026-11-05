# REQ-010 — 経理チーム can view 請求 inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 2 (「請求に関する問い合わせは経理チームでも状況を確認したい」)
- **Type (EARS):** state-driven

## Requirement

While a user is a member of the 経理チーム, the system shall let that user list and open the inquiries whose カテゴリ is 請求.

## Acceptance criteria

1. A test user in the 経理 group (Q14) can open the 問い合わせ管理 list and, by filtering カテゴリ = 請求, sees every inquiry in 請求 (API `get` on the site with that filter returns the same count as for an administrator).
2. The same user can open the edit screen of a 請求 inquiry and sees 状況, 対応担当, 対応期限 and 問い合わせ内容 (API `get` on the record → HTTP 200).
3. A user who is neither in the 経理 group nor otherwise permitted still gets no access (HTTP 404 on the site — KB D19), i.e. the change grants rights to the 経理 group only.
4. *(Visibility of inquiries in other categories is not specified here — `[assumed]` 経理 may see all inquiries read-only, Q13. Restricting 経理 to 請求 only depends on a Pleasanter capability not in the knowledge base — EP-5.)*

## Notes (for P2)

- Read-only access is site permission value 1 (KB D19). Site permissions are not yet in git (no `config/inquiries/permissions.json`) and the 経理 principal is not in `environments.json` — EP-3, EP-4.
- With value 1 the user can also read site settings through `getsite` (D19/D5); configuration contains no secrets (DES-000), so acceptable — to be noted at G2.
