# REQ-012 — 経理チーム can view 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 2: 「対応履歴も見られると助かるそうです」)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall let members of 経理チーム view the 対応履歴 records of the inquiries they can view.

## Acceptance criteria

1. A test user who belongs only to 経理チーム can read the 対応履歴 records linked to a 請求 inquiry (API `get` on the 対応履歴 site filtered by 問い合わせ returns them).
2. The same user sees those records from the 請求 inquiry's screen (linked records). *(Checked by a person on the screen.)*
3. The same user can read 対応内容, 対応日時, 対応者, 作業時間 and 添付資料 of such a record `[assumed]` (Q14).
4. What the support team can see and do on the 対応履歴 site is unchanged.

## Notes

- The customer wrote 「見られると助かる」 (would help): G1 decides whether it is in scope for 12/10 (Q23). It is written as a normal requirement, not dropped.
- The scope follows REQ-010 and Q12: with the assumed site-wide read access, 経理チーム can read every 対応履歴 record. 対応履歴 has no category of its own; limiting it to the history of 請求 inquiries is not covered by the knowledge base and would have to be probed by P2 (see `index.md`, "Points for P2").
- For P2: KB D19 — child sites that inherit the parent's permissions are readable with the same Read permission. Whether `responses` inherits its permissions from `inquiries` today is not in `config/`.
