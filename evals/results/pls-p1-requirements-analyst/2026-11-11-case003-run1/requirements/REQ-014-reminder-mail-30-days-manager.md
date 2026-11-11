# REQ-014 — Mail to 総務課長 30 days before 契約終了日 while still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A7
- **Type (EARS):** complex (state-driven + event-driven)

## Requirement

While a contract is in 有効, when the date is 30 days before its 契約終了日, the system shall send a mail to the 総務課長.

## Acceptance criteria

1. For a contract in 有効 with 契約終了日 = D, a mail addressed to the 総務課長 is sent on the day D − 30 days.
2. For a contract in 更新検討中 or 更新済 with the same date, no such mail is sent.
3. For a contract in 解約, no such mail is sent (REQ-015).
4. The mail is sent once for that 契約終了日, and its text is Japanese and names 契約名, 取引先 and 契約終了日 — `[assumed]`, index question 13.
5. *(Not automatically testable: mail delivery, see REQ-013 criterion 6; the test uses a contract whose 契約終了日 is set to today + 30 days.)*

## Notes

- A7: "Nếu đến 30 ngày trước 契約終了日 mà hợp đồng vẫn còn 有効 thì gửi thêm mail cho 総務課長."
- `[unverified]` Same as REQ-013 — index, "For P2", item U1.
