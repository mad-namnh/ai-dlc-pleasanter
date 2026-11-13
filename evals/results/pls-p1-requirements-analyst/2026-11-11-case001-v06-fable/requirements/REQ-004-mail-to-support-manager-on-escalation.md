# REQ-004 — Mail to the サポート責任者 on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md`
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 executes エスカレーション on an inquiry, the system shall send a mail about that inquiry to its サポート責任者.

## Acceptance criteria

1. The recipient is the user set in the existing field サポート責任者 of the escalated inquiry; no other "escalation target" field is introduced. `[assumed]` Q1.
2. The configuration of the escalation carries a mail notice addressed to the サポート責任者 of the inquiry, with a subject and body that identify the inquiry (問い合わせ番号, 件名, 顧客名, 対応期限, 対応担当). `[assumed]` Q9. Testable by reading the site configuration through the API.
3. One escalation leads to one mail to the サポート責任者: the existing notice 「優先度「高」の問い合わせが未対応です」 does not add a second mail for the same escalation. `[assumed]` Q8.
4. An inquiry whose 優先度 is not 「高」 never causes this mail (see REQ-002).
5. *(Not automatically testable: the arrival of the mail in the mailbox of the サポート責任者 cannot be checked through the API. A person checks it on dev: one escalation, one mail, right recipient, right text. Criterion 3 is checked the same way. See open questions Q8 and Q9.)*

## Notes for P2

- Overlap check (procedure step 2): the site already has notification #1 — mail to the サポート責任者 when 状況 or 優先度 changes, on inquiries in the view 未完了, subject 「優先度「高」の問い合わせが未対応です」. It is a notice about changes, not about an escalation, and under the assumption of Q7 (no status change) an escalation does not change the fields it watches. Whether it nevertheless fires when the escalation saves the inquiry is **not in the KB**: P2 must verify it on dev before designing (listed in `index.md`, "Points P2 must verify").
- The subject of notification #1 speaks of 優先度「高」, but its condition (view 未完了) does not filter on 優先度. This is existing behaviour and outside this request; it is reported to the customer in Q8 only as context.
- What happens when サポート責任者 is empty is Q10; the KB has no entry on a mail notice with an empty recipient.
