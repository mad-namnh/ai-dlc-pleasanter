# Requirements index

Source of REQ-001…REQ-021: interview with Lan (coordinator for the customer's 総務部), 2026-11-11 — `sources/2026-11-11-interview-vendor-contracts.md` (idea: `sources/2026-11-11-vendor-contracts-idea.md`). Summary confirmed by Lan on 2026-11-11; the confirmation is not G1. Nothing here is approved.

| ID | Title | Type | Derived from | Status |
|---|---|---|---|---|
| REQ-001 | Contract record and its fields | ubiquitous | — (A2) | awaiting G1 |
| REQ-002 | Required fields 契約名, 取引先, 契約終了日, 担当者 | unwanted behaviour | — (A2) | awaiting G1 |
| REQ-003 | Contract statuses 有効 / 更新検討中 / 更新済 / 解約 | ubiquitous | — (A3) | awaiting G1 |
| REQ-004 | 総務担当 moves a contract to 更新検討中 and to 更新済 | event-driven | — (A3) | awaiting G1 |
| REQ-005 | Only 総務課長 moves a contract to 解約 | unwanted behaviour | — (A3, A5, A11) | awaiting G1 |
| REQ-006 | A contract in 解約 is not reopened | state-driven | — (A3, A11) | awaiting G1 |
| REQ-007 | 総務担当 creates and edits all contracts | ubiquitous | — (A5) | awaiting G1 |
| REQ-008 | 総務課長 views all contracts | ubiquitous | — (A5) | awaiting G1 |
| REQ-009 | 各部門の担当者 see only the contracts of their own 担当部門 `[unverified]` | ubiquitous | — (A5) | awaiting G1 |
| REQ-010 | 各部門の担当者 change nothing | unwanted behaviour | — (A5) | awaiting G1 |
| REQ-011 | Reminder mail to 担当者 60 days before 契約終了日 `[unverified]` | complex | — (A6, A9) | awaiting G1 |
| REQ-012 | Further mail to 総務課長 30 days before 契約終了日 while still 有効 `[unverified]` | complex | — (A6, A9) | awaiting G1 |
| REQ-013 | Reminder on the Microsoft Teams channel of 総務部 (optional) `[unverified]` | optional | — (A6, A7, A15) | awaiting G1 |
| REQ-014 | 契約終了日 must be after 契約開始日 | unwanted behaviour | — (A12) | awaiting G1 |
| REQ-015 | 月額 is a whole number of yen, 0 or more `[unverified]` | unwanted behaviour | — (A12) | awaiting G1 |
| REQ-016 | Checkbox 「更新確認済」 on every contract | ubiquitous | — (A13) | awaiting G1 |
| REQ-017 | List of contracts ending within 90 days, sorted by 契約終了日 `[unverified]` | ubiquitous | — (A13) | awaiting G1 |
| REQ-018 | 総務担当 see the contracts ending within 90 days that are still 有効 `[unverified]` | ubiquitous | — (A16, need behind C1) | awaiting G1 |
| REQ-019 | Total of 月額 per 取引先 | ubiquitous | — (A7, A13) | awaiting G1 |
| REQ-020 | Contracts in force are in the app on the first day | ubiquitous | — (A7) | awaiting G1 |
| REQ-021 | The 90-day list shows a 各部門の担当者 only the own department's contracts `[unverified]` | state-driven | REQ-009 → REQ-017 (A5, A13) | awaiting G1 |

## Open questions for the customer (お客様への確認事項)

Questions 1–15 are the open points of the interview summary (same numbers); Lan said she will ask 総務部. An assumption is the default used if nobody answers; it is not agreed and no requirement was written from it.

| # | Question (日本語) | Assumption |
|---|---|---|
| 1 | 契約を更新した場合、契約のレコードはどのように扱いますか？（同じレコードの「契約終了日」を書き換える／新しいレコードを作成する など） | `[assumed]` 総務担当 changes 契約終了日 on the same record. No requirement written. |
| 2 | 「自動更新」が「あり」の契約は、契約終了日を迎えたときにどのように処理しますか？ | `[assumed]` The system does nothing by itself; such contracts are reminded and tracked like any other. No requirement written. |
| 3 | 「更新済」になった契約に対して、その後に行う操作はありますか？ | `[assumed]` None; 更新済 leads to no other status. (REQ-003, REQ-004) |
| 4 | 総務課長が「解約」に変更できるのは、どのステータスの契約ですか？（「更新検討中」のみ／「有効」と「更新検討中」／すべて） | `[assumed]` Only from 更新検討中. (REQ-005) |
| 5 | 契約の「担当者」はどなたですか？（総務担当／総務課長／各部門の担当者／それ以外）Pleasanter のユーザーとして登録される方ですか？ | `[assumed]` A Pleasanter user with a mail address, of any group. (REQ-001, REQ-011) |
| 6 | 契約終了日の60日前に契約が「更新検討中」または「更新済」の場合も、担当者へメールを送りますか？ また30日前に「更新検討中」の場合、総務課長へメールを送りますか？ | `[assumed]` 60-day mail for every contract except 解約; 30-day mail only while 有効. (REQ-011, REQ-012) |
| 7 | 総務部の Microsoft Teams チャネルには、どの内容を、どのタイミングで表示しますか？ | `[assumed]` Same content and moment as the 60-day mail; after the first release. (REQ-013) |
| 8 | 取引先ごとの月額合計は、どなたが、何のために確認しますか？ 「解約」の契約も合計に含めますか？ | `[assumed]` Read by 総務担当 and 総務課長; contracts not in 解約; after the first release. (REQ-019, REQ-021) |
| 9 | 契約の一覧で、ほかに必要な絞り込み条件はありますか？ 一覧をファイルに出力（エクスポート）する必要はありますか？ | `[assumed]` No further filter, no export. (REQ-017) |
| 10 | 「更新確認済」のチェックは、どなたが、どのタイミングで付けますか？ | `[assumed]` A 総務担当, at any time. (REQ-016) |
| 11 | 「契約終了日まで90日以内で『有効』のままの契約」の一覧をステータスで実現する場合、「更新確認済」チェックボックスは引き続き必要ですか？ | `[assumed]` Yes, as asked in A13. (REQ-016) |
| 12 | 契約を削除できる方はいますか？ また、総務課長は契約の内容を編集しますか？ | `[assumed]` Nobody deletes; 総務課長 only views and moves to 解約. (REQ-007, REQ-008) |
| 13 | 「更新検討中」の契約を「有効」に戻すことはありますか？ | `[assumed]` No. (REQ-004) |
| 14 | 初回に移行する約140件の契約は、どのステータスで登録しますか？ | `[assumed]` All 有効. (REQ-020) |
| 15 | 「担当部門」が未入力の契約は、どの部門の担当者が閲覧できますか？ | `[assumed]` No 各部門の担当者 sees it. (REQ-009) |
| 16 | 必須項目（契約名・取引先・契約終了日・担当者）のチェックは編集画面での入力時のみでよいですか？（一括取込みや外部連携での登録時もチェックが必要ですか？） | `[assumed]` Screen only (KB D27). (REQ-002) |
| 17 | 契約開始日と契約終了日が同じ日の場合は登録不可でよいですか？ 契約開始日が未入力の場合、日付の前後チェックは行わなくてよいですか？ | `[assumed]` Same day refused; no check when 契約開始日 is empty. (REQ-014) |
| 18 | 新しく登録した契約のステータスは「有効」から始まる、でよいですか？ | `[assumed]` Yes. (REQ-003) |

## Constraints for P2

| # | Constraint | KB entry | Asked for | Need stated instead |
|---|---|---|---|---|
| C1 | A list cannot be filtered on "checkbox not ticked" (checkbox filters are 2-state) | D9 (1.5.2) | List of contracts whose 「更新確認済」 is not ticked (A13) | REQ-018 (A16): contracts ending within 90 days still in 有効, by status |

## To verify in P2 before designing (`[unverified]`)

The person asked for these; the knowledge base has no entry that shows Pleasanter 1.5.x can do them. They are requirements, not promises. Probe on dev, record the result in the KB.

| Point | KB state | Requirements |
|---|---|---|
| A mail sent a set number of days before a date in a record (60 / 30 days before 契約終了日), with a condition on status | Notifications on record change and tenant-level scheduled scripts (D31) only; nothing on date-based reminders | REQ-011, REQ-012 |
| A message on a Microsoft Teams channel | Notification type mail only | REQ-013 |
| Limiting which records of one site a user can see, by the record's 担当部門 | Permissions per site (D15, D19) and per process (D20) only | REQ-009, REQ-021 |
| A list filter "date within the next 90 days" | View sorter and `Overdue` (D24) only | REQ-017, REQ-018 |
| Refusing a number that is negative or not whole | No entry on numeric input limits | REQ-015 |

## Scope and deadline (for G1)

- The app must work before 2027-04-01 (A7). About 15 new contracts a month, 12 users (A7).
- The person said two items may come after the first release if time is short: REQ-013 (Teams) and REQ-019 (total of 月額 per 取引先) (A7, A14). Not decided.
- Not known to the person and not needed for a requirement: how 総務部 works step by step today (A1) and how they learn of an expiry today (A6).
- Derived requirements: new app, nothing runs yet; the only one is REQ-021 (impact of REQ-009 on REQ-017).
