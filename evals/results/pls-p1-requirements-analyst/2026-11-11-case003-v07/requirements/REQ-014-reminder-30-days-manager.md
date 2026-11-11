# REQ-014 — Mail to 総務課長 30 days before 契約終了日 while still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A5, A11`
- **Type (EARS):** complex (event-driven + state)

## Requirement

When a contract's 契約終了日 is 30 days away and the contract is still 有効, the system shall send a mail to the 総務課長.

## Acceptance criteria

1. A 有効 contract with 契約終了日 = today + 30 days: on that day one mail naming the contract (`[assumed]`, index #23) is sent to the 総務課長.
2. A 解約 contract with 契約終了日 = today + 30 days: no mail.
3. A 更新検討中 contract with 契約終了日 = today + 30 days: no mail to the 総務課長 `[assumed]` (index #8).
4. A 更新済 contract with 契約終了日 = today + 30 days: no mail (not 有効).
5. A contract registered when fewer than 30 days remain gets no catch-up mail `[assumed]` (index #10); "30 days" counts calendar days `[assumed]` (index #19).
6. *(Not automatically testable: mail delivery. Test which records are selected on a given day; check one real delivery by hand.)*

## Notes

- `[unverified]`: same as REQ-013 — the KB has no entry on date-based reminders. P2 must verify before designing.
