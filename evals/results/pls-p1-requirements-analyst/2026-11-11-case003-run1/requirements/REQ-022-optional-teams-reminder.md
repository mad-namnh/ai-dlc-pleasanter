# REQ-022 — Optional: reminder in the Microsoft Teams channel of 総務部

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A7, A15
- **Type (EARS):** optional feature

## Requirement

Where the Microsoft Teams reminder is included, the system shall show each reminder about a 契約終了日 in the Microsoft Teams channel of 総務部.

## Acceptance criteria

1. When the mail of REQ-013 is sent for a contract, a message naming 契約名, 取引先 and 契約終了日 appears in the Teams channel of 総務部.
2. When the mail of REQ-014 is sent for a contract, a message appears in the same channel.
3. No message appears for a contract in 解約 (REQ-015).
4. *(Not automatically testable: the Teams channel belongs to the customer and is outside Pleasanter; a person checks the channel. `environments.json` records no side effect for it yet.)*

## Notes

- The person said this is wanted but not mandatory (A7: "nếu làm được thì tốt, không bắt buộc") and may come later (A15). Whether it enters scope at all is for G1: `[assumed]` not in the first release — index question 9.
- `[unverified]` The knowledge base has no entry on sending to Microsoft Teams. P2 must verify — index, "For P2", item U2. A channel address (webhook URL) is a secret and must not be stored in the configuration (project CLAUDE.md rule 4; KB fact 9).
