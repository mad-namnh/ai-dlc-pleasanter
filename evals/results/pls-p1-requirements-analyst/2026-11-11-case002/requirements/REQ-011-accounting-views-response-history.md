# REQ-011 — 経理チーム can view the 対応履歴 of those inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (対応履歴も見られると助かるそうです)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall let members of the 経理チーム open and list the 対応履歴 records linked to inquiries they can view under REQ-010.

## Acceptance criteria

1. A 経理 test user can list the 対応履歴 site, filter it by 問い合わせ, and open each record linked to a 請求 inquiry (API `get` returns the records).
2. The 経理 user sees 対応日時, 対応種別, 作業時間, 対応者 and 対応内容, and can download 添付資料.
3. The visibility scope follows REQ-010 AC 3 and Q13 (`[assumed]` all records).
4. Role test: as REQ-010 AC 5.

## Notes for P2

- KB D19: read rights reach child sites that inherit the parent's permissions; whether 対応履歴 inherits from 問い合わせ or from a folder is not visible in `config/` (PO4).
- 対応履歴 (`responses`) is not in `managed_sites` of `environments.json` (PO2).
