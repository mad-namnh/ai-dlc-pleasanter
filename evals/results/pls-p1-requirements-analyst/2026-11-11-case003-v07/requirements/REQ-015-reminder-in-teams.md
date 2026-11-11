# REQ-015 — Reminder in the 総務部 Teams channel (optional)

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A5` (Lan: 「nếu làm được thì tốt, không bắt buộc」)
- **Type (EARS):** optional feature

## Requirement

Where posting to Microsoft Teams is included, the system shall show each reminder of REQ-013 and REQ-014 in the Teams channel of 総務部.

## Acceptance criteria

1. When a reminder of REQ-013 or REQ-014 is sent, a message naming the contract (契約名, 取引先, 契約終了日 — `[assumed]`, index #23) appears in the 総務部 Teams channel.
2. No message appears for a 解約 contract.
3. Which reminders are posted: both REQ-013 and REQ-014 `[assumed]` (index #21).
4. *(Not automatically testable: delivery to Teams. Checked by hand on a test channel.)*

## Notes

- `[unverified]`: the KB has no entry on posting to Microsoft Teams. P2 must verify before designing; nothing here promises it. If it is designed, any webhook URL is a secret and stays out of configuration (KB fact 9, ADR-0005).
- Optional in Lan's words: dropping it at G1 or P2 does not affect the other requirements.
