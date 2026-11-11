# Requirements index

Source of REQ-001…REQ-021: interview with Lan (customer project coordinator, 総務部), 2026-11-11 — `sources/2026-11-11-interview-vendor-contracts.md`. Lan confirmed the summary the same day; that confirmation is not G1.

| ID | Title | Type | Derived from | Status |
|---|---|---|---|---|
| REQ-001 | One record per vendor contract with its fields | ubiquitous | — (A1) | awaiting G1 |
| REQ-002 | Required contract fields | unwanted behaviour | — (A1) | awaiting G1 |
| REQ-003 | Contract statuses | ubiquitous | — (A3, A10) | awaiting G1 |
| REQ-004 | 総務担当 moves a contract to 更新検討中 | state-driven | — (A3, A4) | awaiting G1 |
| REQ-005 | 総務担当 moves a contract to 更新済 | state-driven | — (A3, A4) | awaiting G1 |
| REQ-006 | 総務課長 moves a contract to 解約 | state-driven | — (A3, A4) | awaiting G1 |
| REQ-007 | Only the 総務課長 may set 解約 | unwanted behaviour | — (A3, A4) | awaiting G1 |
| REQ-008 | A cancelled contract is never reopened `[unverified]` | unwanted behaviour | — (A3, A10) | awaiting G1 |
| REQ-009 | 総務担当 create and edit every contract | ubiquitous | — (A4) | awaiting G1 |
| REQ-010 | 総務課長 views every contract | ubiquitous | — (A4) | awaiting G1 |
| REQ-011 | Department users see only their department's contracts `[unverified]` | ubiquitous | — (A4) | awaiting G1 |
| REQ-012 | Department users cannot change contracts | unwanted behaviour | — (A4) | awaiting G1 |
| REQ-013 | Reminder mail to 担当者 60 days before 契約終了日 `[unverified]` | complex | — (A5, A11) | awaiting G1 |
| REQ-014 | Mail to 総務課長 30 days before 契約終了日 while still 有効 `[unverified]` | complex | — (A5, A11) | awaiting G1 |
| REQ-015 | Reminder in the 総務部 Teams channel (optional) `[unverified]` | optional feature | — (A5) | awaiting G1 |
| REQ-016 | 契約終了日 must be after 契約開始日 | unwanted behaviour | — (A12) | awaiting G1 |
| REQ-017 | 月額 is a whole number of yen, 0 or more `[unverified]` | unwanted behaviour | — (A12) | awaiting G1 |
| REQ-018 | List of contracts ending in the next 90 days `[unverified]` | ubiquitous | — (A13) | awaiting G1 |
| REQ-019 | Total 月額 per 取引先 `[unverified]` | ubiquitous | — (A13) | awaiting G1 |
| REQ-020 | List of contracts ending in 90 days that are still 有効 `[unverified]` | ubiquitous | — (A15, need behind C1) | awaiting G1 |
| REQ-021 | Contracts still in force are in the app from the first day | ubiquitous | — (A7, A14) | awaiting G1 |

**Derived requirements:** none. This is a new app (nothing runs yet), so there is no existing behaviour to protect. Where one requested behaviour affects another, the effect is written into the acceptance criteria of the requirement it touches:
- the department filter of REQ-011 applies to the lists (REQ-018 AC5);
- the 有効-only conditions of REQ-014 and REQ-020 react to status changes (REQ-014 AC3–4, REQ-020 AC3);
- REQ-002 does not protect bulk writes, so the migration must check the required fields itself (REQ-021 AC4).

**Project constraint (A7, A4):**
- The app must be in operation before 2027-04-01.
- About 180 contracts today, about 140 of them in force.
- Users: 総務担当 3, 総務課長 1, 各部門の担当者 about 8 in 6 departments.

## Constraints for P2 (requests Pleasanter cannot meet in the form asked)

| # | What was asked | Why not (KB) | What is required instead |
|---|---|---|---|
| C1 | A 「更新確認済」 tick on each contract and a list of contracts **not** ticked (A13) | A checkbox can be filtered on "checked" only, not on "unchecked" (KB D9, 1.5.2) | Lan's need (A15): a list of contracts ending within 90 days that are still 有効 — REQ-020. Whether the tick itself is still wanted: question #13 |

## Points P2 must verify before designing (`[unverified]` — the KB has no entry)

| Point | Requirements |
|---|---|
| Visibility of records per user by the value of 担当部門 (KB covers per-site rights only, D15/D19) | REQ-011 (and REQ-018 AC5) |
| Mail sent on a date relative to 契約終了日 (60 / 30 days before); KB notifications act on record changes | REQ-013, REQ-014 |
| Posting a message to a Microsoft Teams channel (optional wish) | REQ-015 |
| Refusing every status change out of 解約 (screen and API) | REQ-008 |
| Restricting the change to 解約 to one person on every path (KB D20 covers actions with access control, not the status field itself) | REQ-007 (partly verified) |
| Minimum-value / whole-number check on a number field | REQ-017 |
| A list filtered on a date range relative to today (KB D24 covers "overdue" only) | REQ-018, REQ-020 |
| Totals of a field grouped by another field in a list | REQ-019 |

Nothing in these requirements promises how, or that, these can be done.

## Open questions for the customer (お客様への確認事項)

Lan is asking 総務部 most of these (interview answers marked "pending"). Until a question is answered, its `[assumed]` default is used.

| # | Question (日本語) | Assumption |
|---|---|---|
| 1 | 契約終了日が近づいたとき、総務部では現在どのような手順で対応していますか？誰がどの作業を行いますか？（A2） | `[assumed]` 状態（有効→更新検討中→更新済／解約）の変更以外の手順はない。 |
| 2 | 契約を更新するとき、既存の契約レコードを修正しますか、それとも新しいレコードを登録しますか？（A3） | `[assumed]` 既存レコードを修正する（契約終了日を更新する）。 |
| 3 | 自動更新「あり」の契約は、契約終了日を迎えたときにどのように扱いますか？（A3） | `[assumed]` 自動更新「なし」の契約と同じ扱い（同じ状態、同じリマインド）。 |
| 4 | 契約に関連して、別のファイルや一覧で管理している情報はありますか？（A6） | `[assumed]` なし。取引先は契約ごとに入力する文字項目とする。 |
| 5 | 担当者はどなたですか（総務担当のみ／他部門の方も）？担当者全員が Pleasanter のアカウントとメールアドレスをお持ちですか？（A8） | `[assumed]` 担当者は Pleasanter のユーザーで、メールアドレスを持っている。 |
| 6 | 担当部門は1つの契約につき1部門ですか、複数部門になることがありますか？6部門の一覧は固定ですか？（A9） | `[assumed]` 1契約につき1部門。6部門は固定の一覧から選ぶ。 |
| 7 | 「有効」から直接「解約」に、または「有効」から直接「更新済」に変更することはありますか？「更新検討中」から「有効」に戻すことはありますか？「更新済」の後、契約はどうなりますか？（A10） | `[assumed]` 有効→更新検討中、更新検討中→更新済、更新検討中→解約 の変更のみ。更新済は最終状態。 |
| 8 | 契約終了日の30日前に「更新検討中」の契約について、総務課長へのメールは必要ですか？（A11 (a)） | `[assumed]` 不要（「有効」のときのみ送る）。 |
| 9 | 「更新済」の契約にも、契約終了日の60日前に担当者へメールを送りますか？（A11 (b)） | `[assumed]` 送る（送らないのは「解約」のみ）。 |
| 10 | 契約終了日まで60日（または30日）を切ってから登録・移行された契約にも、メールを送りますか？（A11 (c)） | `[assumed]` 送らない（60日前・30日前の当日にのみ送る）。 |
| 11 | どなたがどの一覧を日次・月次で利用しますか？一覧をファイルに出力する必要はありますか？（A13） | `[assumed]` 契約を閲覧できる人は誰でも一覧を開ける。ファイル出力は不要。 |
| 12 | 移行する約140件の契約は、移行時にどの状態にしますか？移行データは誰が準備しますか？（A14） | `[assumed]` すべて「有効」。移行データは総務部が準備する。 |
| 13 | 「更新確認済」のチェックは、状態「有効」で一覧を見られる場合でも必要ですか？必要な場合、誰がいつチェックし、外すことはありますか？（A13、A15） | `[assumed]` チェック項目は追加しない（REQ-020 の一覧で対応する）。 |
| 14 | 「90日以内に終了する契約」の一覧に、契約終了日を過ぎた契約、「更新済」「解約」の契約を含めますか？（A16） | `[assumed]` 本日から90日後までに終了する契約のみ。「解約」は除き、他の状態は含める。終了日を過ぎた契約は含めない。 |
| 15 | 取引先別の月額合計は、どの契約を対象にしますか？（A17） | `[assumed]` 「解約」以外のすべての契約。 |
| 16 | 総務課長は、「解約」への変更以外に、契約の登録・修正を行いますか？（A4 の確認） | `[assumed]` 行わない（閲覧と解約への変更のみ）。 |
| 17 | 契約終了日と契約開始日が同じ日の契約はありますか？（A12 の確認） | `[assumed]` 同じ日は登録できない（「後」= 翌日以降）。 |
| 18 | 契約開始日が空欄の契約はありますか？その場合、日付の前後チェックはどうしますか？（A12 の確認） | `[assumed]` 契約開始日は任意入力。空欄のときはチェックしない。 |
| 19 | 「60日前」「30日前」は暦日で数えますか、営業日で数えますか？（A5 の確認） | `[assumed]` 暦日。 |
| 20 | 新しく登録した契約の最初の状態は「有効」でよいですか？（A3 の確認） | `[assumed]` 「有効」。 |
| 21 | Teams への通知は、担当者への60日前メールと総務課長への30日前メールの両方が対象ですか？（A5 の確認） | `[assumed]` 両方。 |
| 22 | 契約終了日が契約開始日以前のとき、画面に表示するメッセージは「契約終了日は契約開始日より後の日付を入力してください。」でよいですか？ | `[assumed]` この文言を使う。 |
| 23 | リマインドのメール（および Teams）には、契約名・取引先・契約終了日を記載すればよいですか？ほかに必要な情報はありますか？ | `[assumed]` 契約名・取引先・契約終了日を記載する。 |
