# Interview — vendor contract tracking (総務部)

- **Person:** Lan, coordinates this project for the customer's 総務部 · **Interviewer:** AI (pls-p1-requirements-analyst) · **Date:** 2026-11-11 · **Language:** Vietnamese

## The idea (verbatim)

> Bên tổng vụ (総務部) của khách đang theo dõi hợp đồng với nhà cung cấp bằng Excel, hay bị quên gia hạn. Họ muốn đưa lên Pleasanter để quản lý và được nhắc trước khi hợp đồng hết hạn. Em làm giúp chị nhé.

Given by Lan (customer project coordinator, 総務部), 2026-11-11.

## Before the first question

- Repository: Origin `new`; `config/`, `design/` empty; `requirements/index.md` has no requirements; `environments.json` has `dev` only, no sites. Nothing in the repository answers any area of interview.md section 3.
- Why interview mode: the idea does not say what one record holds, which states a contract passes through, or who may do what (SKILL.md, "When the input is a rough idea").
- KB check (`pls-kb-pleasanter`): mail notifications on a site and on a process exist (schema.md `Notifications[]`, condition = view id). Scheduled reminders ("nhắc trước khi hết hạn" at a date) have **no entry** in the KB — only the flag `IncludeReminders` in site-package headers (api.md). Whatever Lan asks for here is recorded as `[unverified]`, not promised. Required fields are a screen check only (D27). User picker exists (D28). Dev `side_effects.mail` = `unknown`.

## Round 1

Sent 2026-11-11 as one message (Vietnamese). Areas asked: data and fields, life cycle, roles, existing data, reminders. Answers received 2026-11-11 in one message, numbered by question; each numbered part is recorded under its question.

### Q1
Hiện nay trong file Excel, một hợp đồng được ghi như thế nào: mỗi dòng là một hợp đồng hay gì khác, và có những cột thông tin nào? Chị chỉ cần gửi tên các cột (và cột nào bắt buộc phải có), không cần gửi dữ liệu thật của hợp đồng.

**A1** (Lan): Mỗi dòng là một hợp đồng với nhà cung cấp (取引先). Các cột: 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yen), 担当者, 担当部門, và file PDF hợp đồng đính kèm. Bắt buộc phải có: 契約名, 取引先, 契約終了日, 担当者.

### Q2
Khi một hợp đồng sắp hết hạn, hiện nay bên 総務 làm gì, từng bước — từ lúc biết là sắp hết hạn cho đến khi gia hạn xong (hoặc quyết định không gia hạn)? Ai làm từng bước đó?

**A2** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ. Chị chỉ biết là bên đó hay bị quên gia hạn.

→ pending: Lan will ask 総務部.

### Q3
Một hợp đồng được coi là "xong", không cần theo dõi nữa, trong những trường hợp nào? Và khi gia hạn thì hiện nay bên 総務 sửa lại dòng cũ hay thêm một dòng mới?

**A3** (Lan): Một hợp đồng đi theo trạng thái: 有効 → 更新検討中 → 更新済 hoặc 解約. 総務担当 chuyển sang 更新検討中 và 更新済. Chuyển sang 解約 thì chỉ 総務課長 được làm. Hợp đồng đã 解約 thì không mở lại. Còn khi gia hạn thì sửa dòng cũ hay thêm dòng mới, chị không rõ, để chị hỏi lại bên tổng vụ. Riêng hợp đồng 自動更新 thì chị chưa rõ họ muốn xử lý thế nào khi đến ngày hết hạn, để chị hỏi lại.

→ pending in A3: renewal edits the old row or adds a new one; handling of 自動更新 contracts at the end date. Lan will ask 総務部.

### Q4
Ai sẽ nhập và sửa thông tin hợp đồng, ai chỉ cần xem, và có ai (hoặc bộ phận nào) không được phép xem hợp đồng không?

**A4** (Lan): 総務担当 (3 người) tạo và sửa tất cả hợp đồng. 総務課長 (1 người) xem tất cả, và là người duy nhất được chuyển sang 解約. 各部門の担当者 (khoảng 8 người ở 6 bộ phận) chỉ được xem hợp đồng thuộc 担当部門 của mình, không được sửa gì.

KB note: site-level read-only rights are verified (D19, D15); visibility **per record by 担当部門** has no KB entry → `[unverified]`. Restricting a status change to one person: process access control is verified (D20), but that is design, not promised here.

### Q5
Về việc "được nhắc trước khi hợp đồng hết hạn": chị cho em một ví dụ cụ thể — ai cần được nhắc, trước ngày hết hạn bao lâu, nhắc một lần hay nhiều lần, và nhắc qua đâu?

**A5** (Lan): Nhắc bằng mail gửi cho 担当者 trước 契約終了日 60 ngày. Nếu đến trước 契約終了日 30 ngày mà hợp đồng vẫn là 有効 thì gửi thêm một mail cho 総務課長. Hợp đồng 解約 thì không gửi gì. Ngoài ra chị muốn lời nhắc hiện luôn trong kênh Microsoft Teams của 総務部, nếu làm được thì tốt, không bắt buộc.

KB note: date-based reminders (60 / 30 days before 契約終了日) — no KB entry → `[unverified]`. Teams channel — no KB entry → `[unverified]`, optional in Lan's words ("nếu làm được thì tốt, không bắt buộc").

### Q6
Có thông tin nào gắn với hợp đồng mà bên 総務 đang quản lý ở chỗ khác (file khác, danh sách khác) và cần dùng cùng với hợp đồng không?

**A6** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: Lan will ask 総務部.

### Q7
File Excel hiện có khoảng bao nhiêu hợp đồng, và các hợp đồng đó có cần được chuyển sang Pleasanter không? Nếu có thì cần xong trước thời điểm nào?

**A7** (Lan): Khoảng 180 hợp đồng trong một file Excel. Khoảng 140 cái còn hiệu lực thì phải có trong app ngay ngày đầu, còn mấy cái đã 解約 cũ thì không cần chuyển. Phải chạy được trước năm tài chính mới, 2027-04-01.

## Coverage after round 1

| Area | Status |
|---|---|
| Data and fields | partly — fields and required ones (A1); links to other data pending (A6) |
| Life cycle and statuses | partly — statuses, who moves them, 解約 final (A3); today's steps (A2), renewal as edit or new row and 自動更新 handling pending (A3); allowed transitions besides the listed path open |
| Roles and permissions | covered (A4); per-department visibility `[unverified]` |
| Existing data and migration | partly — volume, scope, deadline (A7); how the status of migrated rows is known open |
| Notifications and reminders | partly — recipients, timing, channel (A5); cases for 更新検討中 / 更新済 open |
| Validation rules | open |
| Lists and reports | open |
| Volume and deadline | covered — ~180 rows, ~140 active, users 3 + 1 + ~8 (A4, A7), live before 2027-04-01 (A7) |

## Round 2

Sent 2026-11-11 as one message (Vietnamese). Also tells Lan that per-department visibility, date-based reminders and the Teams message cannot be promised yet (KB silent), and that answers to A2, A3 (pending parts) and A6 are still awaited.

### Q8
担当者 trong hợp đồng thường là ai — luôn là một trong 3 người 総務担当, hay có thể là người ở bộ phận khác? Những người này có tài khoản Pleasanter và địa chỉ mail không?

**A8** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ. Chị cũng không rõ ai có tài khoản Pleasanter hay địa chỉ mail.

→ pending: Lan will ask 総務部.

### Q9
担当部門: một hợp đồng chỉ thuộc một bộ phận, hay có thể thuộc nhiều bộ phận cùng lúc? Danh sách 6 bộ phận có cố định không?

**A9** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: Lan will ask 総務部.

### Q10
Ngoài đường 有効 → 更新検討中 → 更新済 / 解約 chị đã kể: một hợp đồng 有効 có thể chuyển thẳng sang 解約 không, và một hợp đồng 更新検討中 có thể quay lại 有効 không? Sau khi đã 更新済 thì hợp đồng đó tiếp tục thế nào?

**A10** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ. Chị chỉ biết đường đi là 有効 → 更新検討中 → 更新済 hoặc 解約, và 解約 rồi thì không mở lại.

→ pending: other transitions and what follows 更新済; Lan will ask 総務部.

### Q11
Về mail nhắc, chị cho em biết các trường hợp sau sẽ thế nào: (a) hợp đồng đang 更新検討中 khi còn 30 ngày — 総務課長 có nhận mail không; (b) hợp đồng đã 更新済 khi còn 60 ngày — 担当者 có nhận mail không; (c) hợp đồng được nhập vào khi chỉ còn dưới 60 ngày (hoặc dưới 30 ngày) đến 契約終了日?

**A11** (Lan): Chị chỉ biết quy tắc này: còn 30 ngày mà hợp đồng vẫn là 有効 thì gửi thêm mail cho 総務課長. Hợp đồng 解約 thì không gửi gì. Các trường hợp (a), (b), (c) chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: cases (a), (b), (c); Lan will ask 総務部.

### Q12
Khi nhập hoặc sửa hợp đồng, có trường hợp nào bên 総務 muốn hệ thống không cho lưu (thông tin sai, thiếu, mâu thuẫn với thông tin khác) không? Chị cho em ví dụ.

**A12** (Lan): 契約終了日 phải sau 契約開始日. 月額 phải là số nguyên yen, từ 0 trở lên. Ngoài hai điều đó chị chưa biết thêm.

KB note: Pleasanter has no built-in date-order check; refusing such a save needs a script (D25) — a design matter for P2, not a constraint. Integer / minimum-value checks on a number column: no KB entry → `[unverified]`.

### Q13
Hằng ngày hoặc hằng tháng, 総務担当, 総務課長 và 各部門の担当者 cần mở danh sách hợp đồng nào, lọc theo gì, và có cần tính tổng hay xuất ra file không?

**A13** (Lan): Chị cần hai danh sách: hợp đồng sẽ hết hạn trong 90 ngày tới, xếp theo 契約終了日, và tổng 月額 theo từng 取引先. Chị cũng muốn mỗi hợp đồng có ô tick 「更新確認済」, và một danh sách các hợp đồng chưa tick. Còn ai mở danh sách nào hằng ngày hay hằng tháng, và có cần xuất ra file không, chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: who opens which list and how often; export. Lan will ask 総務部.

KB notes:
- A list filtered on "the next 90 days" relative to today: no KB entry (D24 covers only "overdue" on the built-in completion date) → `[unverified]`.
- Total 月額 per 取引先 as a list: no KB entry for grouped totals in a list (D16 / D23 are totals written into a linked parent record) → `[unverified]`.
- The 「更新確認済」 tick and a list of contracts **not** ticked: KB D9 (1.5.2) — a checkbox can be filtered only on "checked", not on "unchecked" → constraint C1, asked in round 3 (Q15).

### Q14
File Excel hiện không có cột trạng thái: khi chuyển khoảng 140 hợp đồng còn hiệu lực sang, mỗi hợp đồng nên ở trạng thái nào, và ai sẽ chuẩn bị dữ liệu để chuyển?

**A14** (Lan): Khoảng 140 hợp đồng còn hiệu lực phải có trong app ngay từ ngày đầu. Các hợp đồng cũ đã kết thúc thì không cần chuyển. Mỗi hợp đồng nên ở trạng thái nào và ai chuẩn bị dữ liệu thì chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: initial status of migrated contracts; who prepares the data. Lan will ask 総務部.

## Coverage after round 2

| Area | Status |
|---|---|
| Data and fields | partly — fields, required ones (A1), 更新確認済 tick wish (A13, see C1); 担当者 identity (A8), 担当部門 cardinality (A9), links (A6) pending |
| Life cycle and statuses | partly — main path, who moves, 解約 final (A3, A10); other transitions, after 更新済, renewal as edit or new row, 自動更新 pending |
| Roles and permissions | covered (A4); per-department visibility `[unverified]` |
| Existing data and migration | partly — volume, scope, deadline (A7, A14); initial status and who prepares data pending |
| Notifications and reminders | partly — rules in A5, A11; cases (a)–(c) pending; recipients' accounts / mail pending (A8) |
| Validation rules | covered as far as known (A12) |
| Lists and reports | partly — two lists and an unticked list (A13); who uses which list, export pending |
| Volume and deadline | covered (A4, A7) |

## Round 3 (last round)

Sent 2026-11-11 as one message (Vietnamese). Short: only points Lan raised in round 2 that she can answer herself, plus how the answers she is collecting from 総務部 reach the requirements. Also tells her that the 90-day list and the total per 取引先 cannot be promised yet (KB silent).

### C1 — constraint (KB D9)
Asked for: a 「更新確認済」 tick on each contract and a list of contracts not ticked (A13). Pleasanter 1.5.2 cannot filter a list on "not ticked", only on "ticked" (KB D9). The need behind it, in Lan's words: *see A15*.

### Q15
(C1) Em xin báo: theo những gì đã được kiểm chứng trên Pleasanter 1.5.2 (mục D9 trong kho kiến thức của dự án), danh sách chỉ lọc được các hợp đồng **đã** tick, không lọc được các hợp đồng **chưa** tick. Vì vậy em muốn hiểu nhu cầu phía sau: ô 「更新確認済」 và danh sách "chưa tick" giúp bên 総務 làm được việc gì? Ai sẽ tick, vào lúc nào, và có khi nào bỏ tick không?

**A15** (Lan): 総務担当 muốn thấy tất cả các hợp đồng sẽ hết hạn trong 90 ngày tới mà chưa chuyển khỏi trạng thái 有効. Dùng trạng thái cũng được, miễn là thấy được danh sách đó. Còn ai tick, tick lúc nào và có bỏ tick không thì chị không rõ, để chị hỏi lại bên tổng vụ.

→ C1 need stated: a list of contracts whose 契約終了日 is in the next 90 days and that are still 有効; status may serve instead of the tick. Pending: who ticks, when, un-ticking; whether the tick itself is still wanted. Lan will ask 総務部.

### Q16
Danh sách "hợp đồng sẽ hết hạn trong 90 ngày tới": hợp đồng đã quá 契約終了日 nhưng chưa xử lý, và hợp đồng đã 更新済 hoặc 解約, có cần hiện trong danh sách này không?

**A16** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: Lan will ask 総務部.

### Q17
"Tổng 月額 theo từng 取引先": tính trên những hợp đồng nào — tất cả, hay chỉ các hợp đồng ở một số trạng thái nhất định?

**A17** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

→ pending: Lan will ask 総務部.

### Q18
Các câu chị đang hỏi lại bên 総務 (câu 2, 6, 8, 9, 10, 11 (a)–(c), 14, một phần câu 3 và câu 13): chị muốn gửi câu trả lời cho em trước khi em viết yêu cầu, hay em ghi chúng thành danh sách câu hỏi mở (bằng tiếng Nhật, kèm giả định tạm của em) để bên 総務 trả lời ở bước duyệt yêu cầu?

**A18** (Lan): Cái đó để chị hỏi lại bên tổng vụ đã, chưa chốt được.

→ not settled. Rounds are used up (interview.md §7): the pending points become open questions with `[assumed]` defaults, as for any unanswered point. Answers that 総務部 sends later are recorded here as new answers and settle the matching open questions.

## Coverage after round 3 (final)

| Area | Status |
|---|---|
| Data and fields | partly — A1; 担当者 identity (A8), 担当部門 cardinality (A9), links (A6), the tick (A13, A15) open |
| Life cycle and statuses | partly — A3, A10; other transitions, after 更新済, renewal as edit or new row, 自動更新 open |
| Roles and permissions | covered (A4); per-department visibility `[unverified]` |
| Existing data and migration | partly — A7, A14; initial status, who prepares data open |
| Notifications and reminders | partly — A5, A11; cases (a)–(c) open; Teams optional `[unverified]` |
| Validation rules | covered as far as known (A12) |
| Lists and reports | partly — A13, A15 (C1); list contents (A16), total basis (A17), who uses which list, export open |
| Volume and deadline | covered (A4, A7) |

No proposals (P<n>) were made in the interview.

## Summary for confirmation

Sent 2026-11-11 in Vietnamese, as below.

> **Mục đích (lời của chị):** Bên 総務部 đang theo dõi hợp đồng với nhà cung cấp bằng Excel và hay bị quên gia hạn; họ muốn quản lý hợp đồng trên Pleasanter và được nhắc trước khi hợp đồng hết hạn.
>
> **Những điểm chị đã xác nhận:**
> 1. *Dữ liệu:* mỗi hợp đồng là một bản ghi, gồm 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yen), 担当者, 担当部門 và file PDF hợp đồng đính kèm; bắt buộc: 契約名, 取引先, 契約終了日, 担当者. (A1)
> 2. *Trạng thái:* 有効 → 更新検討中 → 更新済 hoặc 解約; 総務担当 chuyển sang 更新検討中 và 更新済; chỉ 総務課長 chuyển sang 解約; hợp đồng 解約 không mở lại. (A3, A10)
> 3. *Quyền:* 総務担当 (3 người) tạo và sửa tất cả hợp đồng; 総務課長 (1 người) xem tất cả; 各部門の担当者 (khoảng 8 người, 6 bộ phận) chỉ xem hợp đồng thuộc 担当部門 của mình, không sửa. (A4)
> 4. *Nhắc:* mail cho 担当者 trước 契約終了日 60 ngày; nếu còn 30 ngày mà vẫn 有効 thì thêm mail cho 総務課長; hợp đồng 解約 không gửi gì; nếu làm được thì hiện lời nhắc trong kênh Teams của 総務部 (không bắt buộc). (A5, A11)
> 5. *Kiểm tra khi nhập:* 契約終了日 phải sau 契約開始日; 月額 là số nguyên yen, từ 0 trở lên. (A12)
> 6. *Danh sách:* hợp đồng sẽ hết hạn trong 90 ngày tới, xếp theo 契約終了日; tổng 月額 theo từng 取引先; 総務担当 cần thấy các hợp đồng hết hạn trong 90 ngày tới mà vẫn còn 有効 — dùng trạng thái thay cho ô tick cũng được. (A13, A15)
> 7. *Chuyển dữ liệu:* khoảng 180 hợp đồng trong Excel; khoảng 140 hợp đồng còn hiệu lực phải có trong app từ ngày đầu; hợp đồng đã 解約 cũ không chuyển. (A7, A14)
> 8. *Thời hạn và quy mô:* phải chạy trước 2027-04-01; người dùng 3 + 1 + khoảng 8. (A4, A7)
>
> **Giới hạn đã báo:** C1 — danh sách không lọc được hợp đồng "chưa tick" (D9, Pleasanter 1.5.2); nhu cầu của chị (A15) được ghi thay vào đó.
>
> **Chưa thể hứa (sẽ kiểm tra ở bước thiết kế):** chỉ cho mỗi bộ phận xem hợp đồng của mình; mail nhắc tự động theo ngày (60 / 30 ngày); lời nhắc trong Teams; danh sách 90 ngày tới; tổng 月額 theo 取引先; kiểm tra 月額 là số nguyên từ 0 trở lên.
>
> **Còn mở — em sẽ ghi thành câu hỏi cho bên 総務 (bằng tiếng Nhật), kèm giả định tạm nếu chưa có trả lời:**
> - Các bước hiện nay khi hợp đồng sắp hết hạn (câu 2) → tạm giả định: không có bước nào khác ngoài các trạng thái ở điểm 2.
> - Gia hạn thì sửa bản ghi cũ hay tạo bản ghi mới (câu 3) → tạm giả định: sửa bản ghi cũ (cập nhật 契約終了日).
> - Hợp đồng 自動更新 khi đến ngày hết hạn (câu 3) → tạm giả định: xử lý như mọi hợp đồng khác (cùng trạng thái, cùng lời nhắc).
> - Thông tin liên quan quản lý ở chỗ khác (câu 6) → tạm giả định: không có; 取引先 là một ô nhập chữ trong hợp đồng.
> - 担当者 là ai, có tài khoản Pleasanter và mail không (câu 8) → tạm giả định: 担当者 là người dùng Pleasanter có địa chỉ mail.
> - 担当部門 (câu 9) → tạm giả định: mỗi hợp đồng thuộc đúng một trong 6 bộ phận, danh sách cố định.
> - Các bước chuyển trạng thái khác và sau 更新済 (câu 10) → tạm giả định: chỉ các bước ở điểm 2; 更新済 là trạng thái cuối.
> - Mail nhắc các trường hợp (a) 更新検討中 lúc còn 30 ngày, (b) 更新済 lúc còn 60 ngày, (c) hợp đồng nhập vào khi đã còn dưới 60/30 ngày (câu 11) → tạm giả định theo đúng quy tắc của chị: (a) không gửi cho 総務課長; (b) vẫn gửi cho 担当者 (chỉ 解約 là không gửi); (c) không gửi bù.
> - Ai mở danh sách nào, có cần xuất file không (câu 13) → tạm giả định: mọi người xem được hợp đồng đều mở được các danh sách; không yêu cầu xuất file.
> - Trạng thái ban đầu của 140 hợp đồng chuyển sang và ai chuẩn bị dữ liệu (câu 14) → tạm giả định: tất cả ở 有効; bên 総務 chuẩn bị dữ liệu.
> - Ô 「更新確認済」 có còn cần không, ai tick, khi nào, có bỏ tick không (câu 13, 15) → tạm giả định: không thêm ô tick, vì danh sách theo trạng thái 有効 đáp ứng nhu cầu ở điểm 6.
> - Danh sách 90 ngày tới có gồm hợp đồng đã quá 契約終了日, 更新済, 解約 không (câu 16) → tạm giả định: chỉ hợp đồng có 契約終了日 từ hôm nay đến 90 ngày sau, mọi trạng thái trừ 解約.
> - Tổng 月額 theo 取引先 tính trên hợp đồng nào (câu 17) → tạm giả định: mọi hợp đồng trừ 解約.
>
> Chị xem giúp em bản tóm tắt này có ghi đúng những gì chị đã nói không, và sửa giúp em chỗ nào chưa đúng. Xác nhận này chỉ là "em đã hiểu đúng chị"; các giả định tạm ở trên vẫn là câu hỏi mở, và yêu cầu chỉ được duyệt ở bước G1.

Message as sent also ended with: "Khi bên 総務 trả lời các câu còn mở, chị gửi em để em cập nhật nhé."

**Confirmation** (Lan): Đúng rồi em, chị xác nhận. Mấy điểm còn mở thì đúng là chưa chốt, chị sẽ hỏi lại.

→ The summary reports the interview correctly. The confirmation accepts no proposal (none was made) and settles no open point; it is not G1. The open points become open questions with `[assumed]` defaults in `requirements/index.md` (#1–#21).
