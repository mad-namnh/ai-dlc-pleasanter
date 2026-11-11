# REQ-018 — List of contracts ending within 90 days

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A14
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a list of the contracts whose 契約終了日 falls within the next 90 days, sorted by 契約終了日.

## Acceptance criteria

1. A contract with 契約終了日 = today + 90 days is in the list.
2. A contract with 契約終了日 = today + 91 days is not in the list.
3. With contracts ending at today + 10, + 40 and + 80 days, the list shows them in that order (nearest first) — `[assumed]`, index question 16.
4. A contract whose 契約終了日 is before today is not in the list — `[assumed]`, index question 16.
5. Each user sees in the list only the contracts that user may read (REQ-010, REQ-011).

## Notes

- A14 names no state for this list; it is written as said, for every state. Whether contracts in 解約 or 更新済 belong in it — index question 16.
- `[unverified]` The knowledge base has no entry on a list filtered by a date relative to today other than the overdue list (D24). P2 must verify — index, "For P2", item U4.
