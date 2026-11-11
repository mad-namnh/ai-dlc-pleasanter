# REQ-010 — 経理チーム can view 請求 inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 2)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall let members of 経理チーム view the inquiries whose カテゴリ is 請求, including their 状況.

## Acceptance criteria

1. A test user who belongs only to 経理チーム can open the list of the 問い合わせ site and, with the カテゴリ filter set to 請求, sees the 請求 inquiries with their 状況 (API `get` with that user returns them).
2. The same user can open one 請求 inquiry and read its fields `[assumed]` (Q14: all fields, including 顧客名, 問い合わせ内容, AI: 回答の下書き and 添付資料).
3. A user who belongs neither to the support team nor to 経理チーム still cannot open the site (unchanged).
4. What the support team can see and do on the site is unchanged.

## Notes

- **Access scope is an open decision (Q12).** This requirement is written with the assumption `[assumed]` that 経理チーム may also see inquiries of other categories (read access for the whole site). The mail states a need ("wants to check 請求 inquiries"), not a restriction. This default **widens access to all inquiries**; G1 must decide it explicitly, it must not pass unnoticed.
- If the answer to Q12 is "経理 must see 請求 inquiries only": the knowledge base has no entry on restricting read access per record by a column value. That is not verified and is not promised here; P2 must probe it on dev before designing (listed in `index.md`, "Points for P2").
- Until REQ-008 is done, past invoice inquiries still hold 契約・請求 and are not found by カテゴリ = 請求.
- For P2: KB D19 — site permission value 1 (Read) gives read access to records, attachments (download) and `getsite` (site settings). Verified on 1.5.2. The principal `accounting` already exists in `environments.json` (dev, stg); the current site permissions are not in `config/` (no `permissions.json`) — P2 must read them before designing (Q13).
