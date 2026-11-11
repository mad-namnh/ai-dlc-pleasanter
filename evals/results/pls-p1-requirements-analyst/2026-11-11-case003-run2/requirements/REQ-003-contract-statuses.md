# REQ-003 — Contract statuses

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A3
- **Type (EARS):** ubiquitous

## Requirement

The system shall give every contract exactly one of the statuses 有効, 更新検討中, 更新済 and 解約.

## Acceptance criteria

1. The status of a contract offers the four values 有効, 更新検討中, 更新済, 解約 and no other.
2. A newly created contract has the status 有効 (`[assumed]` — A3 gives 有効 as the first state but does not say it is set on creation — question 18).

## Notes for P2

- Not answered and therefore not required here: what happens to a 自動更新 contract at its 契約終了日 (question 2); what follows 更新済 (question 3); how a renewal changes the record (question 1); whether 更新検討中 may return to 有効 (question 13).
