# Requirements index

Source of REQ-001 … REQ-022: `sources/2026-11-11-interview-vendor-contract-management.md` (interview with Lan, 2026-11-11; idea in `sources/2026-11-11-vendor-contract-management.md`). Purpose as the person confirmed it (A18): 総務部 tracks its contracts with vendors in Excel and wants to be reminded before a contract expires.

All requirements are **awaiting G1**. The interview confirmation is not an approval; the person said the approval is Nam's decision (G1 approver in the project profile).

| ID | Title | Type | Derived from | Status |
|---|---|---|---|---|
| REQ-001 | Contract record and its items | ubiquitous | — (A2) | awaiting G1 |
| REQ-002 | Required items | unwanted behaviour | — (A2) | awaiting G1 |
| REQ-003 | States of a contract | ubiquitous | — (A3) | awaiting G1 |
| REQ-004 | 総務担当 moves a contract to 更新検討中 | event-driven | — (A3) | awaiting G1 |
| REQ-005 | 総務担当 moves a contract to 更新済 | event-driven | — (A3) | awaiting G1 |
| REQ-006 | 総務課長 moves a contract to 解約 | event-driven | — (A3, A6, A9) | awaiting G1 |
| REQ-007 | Only 総務課長 may move a contract to 解約 | unwanted behaviour | — (A3, A6, A9) | awaiting G1 |
| REQ-008 | A contract in 解約 is not reopened | unwanted behaviour | — (A3) | awaiting G1 |
| REQ-009 | 総務担当 create and change all contracts | ubiquitous | — (A6) | awaiting G1 |
| REQ-010 | 総務課長 reads all contracts | ubiquitous | — (A6) | awaiting G1 |
| REQ-011 | 各部門の担当者 see only their department's contracts | ubiquitous | — (A6) | awaiting G1 |
| REQ-012 | 各部門の担当者 change nothing | unwanted behaviour | — (A6) | awaiting G1 |
| REQ-013 | Reminder mail to 担当者 60 days before 契約終了日 | event-driven | — (A7) | awaiting G1 |
| REQ-014 | Mail to 総務課長 30 days before 契約終了日 while still 有効 | complex | — (A7) | awaiting G1 |
| REQ-015 | No reminder for a contract in 解約 | unwanted behaviour | — (A7, A11) | awaiting G1 |
| REQ-016 | 契約終了日 must be after 契約開始日 | unwanted behaviour | — (A13) | awaiting G1 |
| REQ-017 | 月額 is a whole number of yen, 0 or more | unwanted behaviour | — (A13) | awaiting G1 |
| REQ-018 | List of contracts ending within 90 days | ubiquitous | — (A14) | awaiting G1 |
| REQ-019 | List for 総務担当: ending within 90 days and still 有効 | ubiquitous | — (A16, need behind C1) | awaiting G1 |
| REQ-020 | Total 月額 per 取引先 | ubiquitous | — (A14, A15) | awaiting G1 |
| REQ-021 | Contracts still in force are present on the first day | ubiquitous | — (A12) | awaiting G1 |
| REQ-022 | Optional: reminder in the Microsoft Teams channel of 総務部 | optional feature | — (A7, A15) | awaiting G1 |

**Derived requirements:** none. This is a new app: nothing runs yet, so there is no existing behaviour to protect, and no requested behaviour was found to change another requested one beyond what the requirements already state (REQ-015 names the reminders it applies to; REQ-019 names the move of REQ-004). Everything else the app might need is a question below.

**Project constraint (not a system behaviour):** the system must be usable before 2027-04-01, the start of the customer's new fiscal year (A12, A15). Volume: about 15 new contracts a month, 12 users (A15).

## Open questions for the customer (お客様への確認事項)

Questions 1–9 are points the person could not answer in the interview and will ask 総務部. Questions 10–16 are points nobody was asked or that needed interpretation. An assumption is what P1 uses until the customer answers; it is not agreed.

| # | Question (日本語) | Assumption |
|---|---|---|
| 1 | 契約の「担当者」には、どなたを設定しますか（総務担当、各部門の担当者、またはその他の方）。 | `[assumed]` Any user of the system can be chosen as 担当者. (A10 not answered; REQ-001, REQ-013) |
| 2 | 「更新済」にした後、次の契約期間はどのように管理しますか（同じ契約の「契約終了日」を書き換える／新しい契約として登録する／その他）。 | `[assumed]` 更新済 is the last state of that record; the next term is entered as a new contract. (A8 not answered; REQ-003, REQ-005) |
| 3 | 「解約」への変更は、どの状態の契約に対して行えますか（「更新検討中」のみ／「有効」と「更新検討中」／「更新済」を含むすべて）。 | `[assumed]` From 有効 and 更新検討中, not from 更新済. (A9 not answered; REQ-006) |
| 4 | 「自動更新」が「あり」の契約は、期限前の通知や状態の変更をどのように扱いますか。 | `[assumed]` Handled like every other contract: same states, same reminders. (A4 not answered; REQ-003, REQ-013) |
| 5 | 契約終了日の60日前に担当者へ送るメールは、「解約」以外に送らない場合がありますか（例：「更新検討中」「更新済」の契約）。 | `[assumed]` Only contracts in 解約 are excluded. (A11 not answered; REQ-013) |
| 6 | 現在のExcelに添付されている契約書PDFも、新しいシステムへ移行しますか。移行する場合、いつまでに必要ですか。 | `[assumed]` Not carried over on the first day; attached by hand afterwards. (A12 not answered for PDF; REQ-021) |
| 7 | 契約の一覧をファイル（Excel／CSV）に出力する必要はありますか。必要な場合、どなたが出力しますか。 | `[assumed]` No export is needed. No requirement is written. (A14 not answered) |
| 8 | チェックボックス「更新確認済」は必要ですか。必要な場合、どなたが、どのタイミングでチェックしますか。なお「未チェックの契約一覧」はPleasanterの制約により作成できないため、「90日以内に終了し、まだ『有効』の契約一覧」で代替します。 | `[assumed]` The checkbox is not built; the list of REQ-019 covers the need. No requirement is written for the checkbox. (A14, A16, A17; constraint C1) |
| 9 | 「取引先ごとの月額合計」と「Microsoft Teamsへの通知」は、初回リリースに含めますか、後のリリースにしますか。また、月額合計には「解約」の契約も含めますか。 | `[assumed]` Both come after the first release; the total counts every contract. (A15; REQ-020, REQ-022) |
| 10 | Excelから移行する有効な契約（約140件）は、すべて「有効」の状態で登録してよいですか。 | `[assumed]` All carried-over contracts are in 有効. (REQ-021) |
| 11 | 新しく登録した契約の最初の状態は「有効」でよいですか。 | `[assumed]` A new contract starts in 有効. (REQ-003) |
| 12 | 総務課長は、契約の新規登録・項目の変更・「更新検討中」「更新済」への変更も行いますか。それとも閲覧と「解約」への変更のみですか。 | `[assumed]` 総務課長 reads everything and moves contracts to 解約; nothing else. (A6; REQ-004, REQ-005, REQ-010) |
| 13 | 通知メールは契約終了日ごとに1回の送信でよいですか。また、件名と本文に記載したい内容はありますか。 | `[assumed]` One mail per contract and date; Japanese text naming 契約名, 取引先 and 契約終了日. (REQ-013, REQ-014) |
| 14 | 「取引先」と「担当部門」は自由入力ですか、それとも一覧から選択しますか。 | `[assumed]` 取引先 is free text as in the Excel file; 担当部門 is chosen from the customer's departments. (REQ-001) |
| 15 | 契約終了日が契約開始日より後でない場合のエラーメッセージは「契約終了日は契約開始日より後の日付にしてください。」でよいですか。また、契約開始日が未入力の場合はこのチェックを行わなくてよいですか。 | `[assumed]` That message; the check applies only when both dates are entered. (REQ-016) |
| 16 | 「90日以内に終了する契約の一覧」は、契約終了日の近い順に並べ、すでに終了日を過ぎた契約は表示しない、でよいですか。また「解約」「更新済」の契約も表示しますか。 | `[assumed]` Nearest date first; contracts past their date are not shown; every state is shown, as the list was described. (A14; REQ-018) |
| 17 | 参考情報として教えてください：現在のExcelでの運用手順（どなたが、いつ入力・確認するか）、契約終了が近づいたときの現在の対応と記録方法、過去に入力を誤った例。 | No assumption — background only; no requirement depends on it. (A1, A4, A5, A13 not answered) |

## For P2 — constraints and points to verify

**Constraint**

| # | Constraint | KB entry | Need stated instead |
|---|---|---|---|
| C1 | A list of contracts where the checkbox 「更新確認済」 is **not** ticked cannot be built: a list can be filtered on "ticked" only. | D9 (1.5.2) | A16 → REQ-019 |

**`[unverified]` — the knowledge base says nothing; P2 must verify on dev before designing, and must not assume**

| # | Wish as the person said it | Requirement |
|---|---|---|
| U1 | A mail sent a fixed number of days (60, 30) before 契約終了日 (A7). The KB has no verified entry on date-based reminders; scheduled background scripts cannot be deployed by `pls` (D31). | REQ-013, REQ-014, REQ-015 |
| U2 | The reminder shown in the Microsoft Teams channel of 総務部 (A7). | REQ-022 |
| U3 | 各部門の担当者 see only the contracts of their own 担当部門 (A6). D19 and D20 cover a whole site and actions, not single records. | REQ-011 |
| U4 | A list filtered on "契約終了日 within the next 90 days" (A14, A16). The KB knows only the overdue list (D24). | REQ-018, REQ-019 |
| U5 | A total of 月額 per 取引先 (A14). The KB knows a total written from child records to a parent (D16). | REQ-020 |
| U6 | Refusing a 月額 that is not a whole number or is below 0 (A13). | REQ-017 |

**Verified KB entries that bear on the requirements**

- D27: "required" is a screen setting only (REQ-002). D17 is the same for read-only.
- D25: the order of two dates is not checked by Pleasanter; refusing needs a server script, which needs a written reason (REQ-016, I5).
- D19, D20: a read-only user still sees an action unless it is restricted to groups (REQ-007, REQ-012).
- D13, D18, D28: loading the existing contracts; 担当者 as a user id per environment (REQ-021).
- `environments.json`: `side_effects.mail` and `jobs` are `unknown` on dev; mail criteria are checked by a person.
