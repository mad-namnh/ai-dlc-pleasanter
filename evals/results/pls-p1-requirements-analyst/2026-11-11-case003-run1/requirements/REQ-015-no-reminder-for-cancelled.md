# REQ-015 — No reminder for a contract in 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A7, A11
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract is in 解約, then the system shall not send any reminder about its 契約終了日.

## Acceptance criteria

1. For a contract in 解約 whose 契約終了日 is today + 60 days, no mail is sent to its 担当者.
2. For a contract in 解約 whose 契約終了日 is today + 30 days, no mail is sent to the 総務課長.
3. A contract moved to 解約 before D − 60 days receives no reminder afterwards.
4. *(Not automatically testable: the absence of a mail cannot be observed through the API; a person checks the mailbox of a test 担当者 and of the test 総務課長.)*

## Notes

- A7: "Hợp đồng 解約 thì không gửi gì."
- Where the optional reminder in Microsoft Teams (REQ-022) is included, this requirement applies to it as well.
