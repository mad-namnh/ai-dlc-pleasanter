# REQ-012 — Further mail to 総務課長 30 days before 契約終了日 while still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A6, A9
- **Type (EARS):** complex (state-driven + event-driven)

## Requirement

While a contract is in 有効, when the date is 30 days before its 契約終了日, the system shall send a mail to 総務課長.

## Acceptance criteria

1. A contract in 有効 whose 契約終了日 is 30 days ahead: one mail is addressed to 総務課長.
2. A contract in 解約 whose 契約終了日 is 30 days ahead: no mail.
3. *(A contract in 更新検討中 at the 30-day point: not answered (A9). `[assumed]` no mail — A6 says "vẫn còn 有効" — question 6.)*
4. *(Not automatically testable: the delivery of the mail and the passing of days; a person checks the received mail on dev.)*

## Notes for P2

- **`[unverified]`** — same reason as REQ-011: the KB has no entry on a reminder sent a set number of days before a date. P2 must verify before designing. Listed in `index.md` under "To verify in P2".
