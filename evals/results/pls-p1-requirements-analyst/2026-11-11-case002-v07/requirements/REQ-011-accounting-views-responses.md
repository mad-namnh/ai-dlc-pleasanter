# REQ-011 — 経理チーム can view 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (対応履歴も見られると助かるそうです)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall let members of the 経理チーム view the response records of the inquiries they may view.

## Acceptance criteria

1. A test user in the 経理チーム group opens a 請求 inquiry's response records (list filtered by 問い合わせ, and the edit screen of one record) and reads 対応種別, 対応日時, 作業時間, 対応者, 対応内容 and attachments.
2. Scope of other response records follows Q15 (`[assumed]`: all response records are readable, consistent with Q14).

## Notes

- The customer wrote 「助かる」 (nice to have); kept as a requirement because it is a direct request; G1 may scope it.
- For P2: `environments.json` lists only `inquiries` in `managed_sites`; 対応履歴 (`responses`) is not managed although its configuration is in `config/`. This requirement and REQ-012/013 change that site — see project-owner question PO-1.
