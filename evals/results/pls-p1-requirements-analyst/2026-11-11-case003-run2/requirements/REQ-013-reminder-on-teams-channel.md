# REQ-013 — Reminder shown on the Microsoft Teams channel of 総務部 (optional)

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A6, A7, A15
- **Type (EARS):** optional

## Requirement

Where reminding on Microsoft Teams is included, the system shall show the reminder of a contract nearing its 契約終了日 on the Microsoft Teams channel of 総務部.

## Acceptance criteria

1. With the feature included, a reminder for a contract appears as a message on the 総務部 channel.
2. *(What the message contains and when it appears: not answered (A15). `[assumed]` the same content and moment as the 60-day mail of REQ-011 — question 7.)*
3. *(Not automatically testable: a person reads the channel.)*

## Notes for P2

- **`[unverified]`** — the KB knows notification type mail only; it has no entry on Microsoft Teams. Nobody has shown that Pleasanter 1.5.x can do this; P2 must verify before designing. Listed in `index.md` under "To verify in P2".
- The person called it not mandatory (A6, A15) and said it may come after the first release if time is short (A7). Whether it is in the first release is for G1 to decide.
- A Teams channel address (webhook URL) is a secret: it must not be stored in the configuration (project rule 4).
