# REQ-010 — 経理チーム can view billing inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (請求に関する問い合わせは経理チームでも状況を確認したい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall let members of the 経理チーム view the inquiries whose カテゴリ is 請求, including their 状況.

## Acceptance criteria

1. A test user in the 経理チーム group (Q13) can open the list and filter カテゴリ = 請求; every 請求 inquiry is listed with its 状況.
2. The same user can open the edit screen of a 請求 inquiry and read its fields and attachments (KB D19: read permission).
3. Whether the user can also see inquiries of other categories follows the answer to Q14 (`[assumed]`: yes — see note).

## Notes

- Depends on REQ-007 (請求 exists as a category only after the split) and, for past inquiries, on REQ-008.
- **Visibility of other categories (Q14):** site-level read permission is verified (KB D19); limiting a reader to the records of one category is **not** in the KB (record permissions appear only as a package flag, behaviour unverified). The default `[assumed]` is therefore "経理 can read all inquiries"; if the customer answers that other categories must be hidden, P2 must probe that on dev before it is promised. The default exposes customer names and inquiry text of all categories to 経理 — the customer must decide this explicitly.
- No new view is requested; whether 経理 wants a ready-made 請求 list is part of Q14 (`[assumed]` no — they use the カテゴリ filter).
- For P2: no `permissions.json` exists in `config/` for either site, and `environments.json` names no principal besides admin — current permissions are not in git.
