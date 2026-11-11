# Interview — vendor contract management

- **Person:** Lan, project coordinator for the customer's 総務部 · **Interviewer:** AI (pls-p1-requirements-analyst) · **Date:** 2026-11-11 · **Language:** Vietnamese

## The idea (verbatim)

> Bên tổng vụ (総務部) của khách đang theo dõi hợp đồng với nhà cung cấp bằng Excel, hay bị quên gia hạn. Họ muốn đưa lên Pleasanter để quản lý và được nhắc trước khi hợp đồng hết hạn. Em làm giúp chị nhé.

## Before the first question (interviewer notes, not answers)

- Why interview mode: the idea names a goal and does not say what one record is and its fields, the states a record goes through, or who may do what.
- Repository: `config/` and `design/` are empty, `requirements/index.md` has no entry, `environments.json` has `dev` only with no sites. New app; nothing in the repository answers a question.
- `pls-kb-pleasanter` per area:
  - Data and fields: a user picker is available (D28); "required" is a screen setting only (D27).
  - Life cycle: statuses; a list of records past their date and not completed exists (D24).
  - Roles: read-only role is possible (D19); actions can be hidden per group (D20).
  - Notifications and reminders: mail notification on a record change with a view as condition is in the KB (`references/schema.md`). **The KB has no verified entry on a reminder sent a number of days before a date** (only the site-package flag `IncludeReminders` is mentioned). A wish for it is `[unverified]` for P2. Scheduled background scripts cannot be deployed by `pls` (D31). `environments.json` `side_effects.mail` is `unknown` on dev.
  - Existing data: bulk upsert keyed on a business identifier exists (D13, D18).

## Round 1

Sent 2026-11-11. Area coverage before the round: all eight areas open.

### Q1
Hiện tại bên tổng vụ theo dõi hợp đồng trong file Excel như thế nào, từng bước một: ai nhập, nhập lúc nào, và ai mở file ra xem, vào dịp nào?

**A1** (Lan): Hiện giờ bên tổng vụ chỉ giữ file Excel này, chị chưa có thông tin chi tiết về từng bước ai nhập lúc nào, ai mở xem vào dịp nào. Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q2
Một dòng trong file Excel đó là gì (một hợp đồng, một lần gia hạn, hay cái khác), và trên một dòng có những cột thông tin nào? Trong đó cột nào bắt buộc phải có?

**A2** (Lan): Một dòng là một hợp đồng với một nhà cung cấp (取引先). Các cột hiện có: 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yên), 担当者, 担当部門, và file PDF hợp đồng đính kèm. Bắt buộc phải có: 契約名, 取引先, 契約終了日, 担当者.

### Q3
Một hợp đồng đi qua những giai đoạn nào kể từ lúc ký cho đến lúc không còn theo dõi nữa? Ai là người chuyển nó từ giai đoạn này sang giai đoạn kế tiếp?

**A3** (Lan): Hợp đồng đi qua: 有効 → 更新検討中 → 更新済 hoặc 解約. 総務担当 là người chuyển sang 更新検討中 và sang 更新済. Chuyển sang 解約 thì chỉ 総務課長 được làm. Hợp đồng đã 解約 thì không mở lại nữa.

### Q4
Khi một hợp đồng sắp hết hạn, hiện nay người ta làm gì với nó, và sau khi xử lý xong thì hợp đồng đó được ghi lại trong file ra sao?

**A4** (Lan): Phần xử lý khi sắp hết hạn và cách ghi lại trong file thì chị không rõ, để chị hỏi lại bên tổng vụ. Riêng hợp đồng 自動更新 thì chị chưa rõ họ muốn xử lý thế nào, để chị hỏi lại.

### Q5
Chị kể giúp em một lần gần đây bị quên gia hạn: chuyện gì đã xảy ra, và lẽ ra ai cần biết, vào lúc nào?

**A5** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q6
Những ai sẽ làm việc với dữ liệu hợp đồng này: ai tạo mới, ai sửa, ai chỉ xem, và có ai không được phép thấy (toàn bộ hoặc một phần thông tin) không?

**A6** (Lan): 総務担当 (3 người): tạo và sửa tất cả hợp đồng. 総務課長 (1 người): xem tất cả, và là người duy nhất được chuyển sang 解約. 各部門の担当者 (khoảng 8 người ở 6 phòng ban): chỉ xem hợp đồng của 担当部門 mình, không sửa gì.

### Q7
Về việc "được nhắc trước khi hợp đồng hết hạn": ai cần được nhắc, trước bao lâu, và họ muốn nhận lời nhắc bằng cách nào?

**A7** (Lan): Gửi mail cho 担当者 trước 契約終了日 60 ngày. Nếu đến 30 ngày trước 契約終了日 mà hợp đồng vẫn còn 有効 thì gửi thêm mail cho 総務課長. Hợp đồng 解約 thì không gửi gì. Ngoài ra chị muốn lời nhắc hiện cả trong kênh Microsoft Teams của 総務部, nếu làm được thì tốt, không bắt buộc.

### After round 1 (interviewer notes, not answers)

Not answered by the person ("để chị hỏi lại") — stay open, not re-asked, become open questions if no answer arrives:
- A1: how the Excel file is used today, step by step.
- A4: what is done when a contract is about to expire and how it is recorded; how 自動更新 contracts are to be handled.
- A5: an example of a missed renewal.

`[unverified]` wishes (the KB says nothing; neither a constraint nor a promise; for P2 to verify):
- A7: mail sent a fixed number of days (60, 30) before 契約終了日 — no KB entry on date-based reminders.
- A7: reminder shown in the Microsoft Teams channel of 総務部 (the person said optional) — no KB entry.
- A6: 各部門の担当者 see only the contracts of their own 担当部門 — KB entries D19/D20 cover site-level read-only and process access, not visibility per record.

Area coverage:

| Area | State | From |
|---|---|---|
| Data and fields | partly — who the 担当者 is (総務 or department) is not said | A2 |
| Life cycle and statuses | partly — what follows 更新済; from which states 解約 is possible; 自動更新 (person will ask back) | A3, A4 |
| Roles and permissions | covered | A3, A6 |
| Existing data and migration | open | — |
| Notifications and reminders | partly — whether the 60-day mail depends on the state other than 解約 | A7 |
| Validation rules | open (required fields given in A2) | A2 |
| Lists and reports | open | — |
| Volume and deadline | partly — number of users given, rest open | A6 |

## Round 2

Sent 2026-11-11.

### Q8
Sau khi một hợp đồng đã được chuyển sang 更新済, kỳ hợp đồng tiếp theo được theo dõi như thế nào?

**A8** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q9
Việc chuyển sang 解約 được làm từ giai đoạn nào: (a) chỉ từ 更新検討中, (b) từ cả 有効 và 更新検討中, (c) từ bất kỳ giai đoạn nào kể cả 更新済, (d) khác?

**A9** (Lan): Chị chỉ biết việc chuyển sang 解約 thì chỉ 総務課長 được làm. Còn làm được từ giai đoạn nào thì chị không rõ, để chị hỏi lại bên tổng vụ.

### Q10
担当者 ghi trên mỗi hợp đồng là ai: (a) một trong 3 総務担当, (b) 各部門の担当者 của 担当部門 đó, (c) có thể là một trong hai, (d) khác?

**A10** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q11
Mail gửi cho 担当者 trước 契約終了日 60 ngày: ngoài hợp đồng 解約 ra, còn trường hợp nào không được gửi mail này không?

**A11** (Lan): Chị chỉ biết hợp đồng 解約 thì không gửi gì. Ngoài ra có trường hợp nào nữa không thì chị không rõ, để chị hỏi lại bên tổng vụ.

### Q12
File Excel hiện nay có khoảng bao nhiêu hợp đồng, dữ liệu và các file PDF đó có cần được đưa sang hệ thống mới không, và nếu có thì cần xong trước lúc nào?

**A12** (Lan): File Excel có khoảng 180 hợp đồng. Khoảng 140 hợp đồng còn hiệu lực thì phải có trong hệ thống ngay ngày đầu. Các hợp đồng cũ đã 解約 thì không cần. Còn file PDF thì chị không rõ, để chị hỏi lại bên tổng vụ. Hạn là trước năm tài chính mới, 2027-04-01.

### Q13
Khi nhập hoặc sửa một hợp đồng, có trường hợp nhập nào mà hệ thống phải từ chối không? Nếu được, chị cho em một ví dụ nhập sai mà bên tổng vụ từng gặp.

**A13** (Lan): Có hai quy tắc. 契約終了日 phải sau 契約開始日. 月額 phải là số nguyên yên, từ 0 trở lên. Còn ví dụ nhập sai bên tổng vụ từng gặp thì chị không rõ, để chị hỏi lại.

### Q14
Trong công việc hằng ngày hoặc hằng tháng, mọi người cần mở những danh sách hợp đồng nào, lọc hay sắp xếp theo gì, có cần con số tổng nào, và có cần xuất ra file không?

**A14** (Lan): Có hai danh sách. Danh sách thứ nhất là các hợp đồng sắp hết hạn trong 90 ngày, sắp xếp theo 契約終了日. Danh sách thứ hai là tổng 月額 theo từng 取引先. Ngoài ra chị muốn có checkbox 「更新確認済」 trên mỗi hợp đồng, và một danh sách các hợp đồng chưa được tick. Còn việc có cần xuất ra file hay không thì chị không rõ, để chị hỏi lại.

### Q15
Mỗi tháng có khoảng bao nhiêu hợp đồng mới, hệ thống cần dùng được từ ngày nào, và phần nào có thể làm sau?

**A15** (Lan): Mỗi tháng khoảng 15 hợp đồng mới, tổng cộng 12 người dùng. Hệ thống phải dùng được trước 2027-04-01. Phần Teams và phần tổng 月額 có thể làm sau nếu cần.

### Remark with the round 2 reply (unprompted)

(Lan): 1–7 chị đã trả lời ở trên rồi em.

### C1 — constraint (KB D9)

Asked for (A14): a checkbox 「更新確認済」 on each contract, and a list of the contracts that are **not** ticked.
What Pleasanter cannot do (KB D9, verified on 1.5.2): a list can be filtered on "checkbox is ticked" only; "not ticked" cannot be filtered. The checkbox itself is not affected.
What the person needs instead: asked in Q16 — see A16 (her words): "Họ cần thấy mọi hợp đồng sẽ hết hạn trong 90 ngày tới mà vẫn chưa được chuyển khỏi trạng thái 有効. Dùng trạng thái cũng được, miễn là thấy được danh sách đó."

### After round 2 (interviewer notes, not answers)

Not answered by the person ("để chị hỏi lại") — stay open, not re-asked:
- A8: how the next term is followed after 更新済.
- A9: from which states 解約 is possible.
- A10: who the 担当者 on a contract is.
- A11: other cases where the 60-day mail must not be sent.
- A12: whether the PDF files are carried over.
- A13: an example of wrong input.
- A14: whether lists must be exported to a file.

`[unverified]` wishes added (the KB says nothing; for P2 to verify):
- A14: a list of contracts ending within 90 days (a date filter relative to today).
- A14: total 月額 per 取引先 (the KB knows a total written to a parent record, D16; whether that fits depends on the design).
- A13: refusing 月額 that is not a whole number of yen or is below 0.

KB entries that apply to answers (notes for P2, not requirements):
- A13, 契約終了日 after 契約開始日: no built-in date-order check; it needs a script (D25).
- A2, required fields: required is a screen setting only (D27).
- A12, carrying over about 140 contracts: bulk upsert on a unique business key (D13, D18).

Area coverage:

| Area | State | From |
|---|---|---|
| Data and fields | partly — 担当者 open (person will ask back) | A2, A10 |
| Life cycle and statuses | partly — after 更新済, origin states of 解約, 自動更新 open (person will ask back) | A3, A4, A8, A9 |
| Roles and permissions | covered | A3, A6 |
| Existing data and migration | covered, PDF files open | A12 |
| Notifications and reminders | covered, other exclusions open | A7, A11 |
| Validation rules | covered | A2, A13 |
| Lists and reports | partly — constraint C1 on the "not ticked" list; export open | A14 |
| Volume and deadline | covered | A12, A15 |

## Round 3

Sent 2026-11-11. Last round; shorter because only the point of C1 is open and can be asked.

### Q16
Danh sách "các hợp đồng chưa được tick 更新確認済" sẽ giúp bên tổng vụ làm được việc gì: ai mở danh sách đó, và họ cần thấy những hợp đồng nào trong đó?

**A16** (Lan): 総務担当 là người mở danh sách đó. Họ cần thấy mọi hợp đồng sẽ hết hạn trong 90 ngày tới mà vẫn chưa được chuyển khỏi trạng thái 有効. Dùng trạng thái cũng được, miễn là thấy được danh sách đó.

### Q17
Ô 「更新確認済」 do ai tick, và tick vào lúc nào trong quá trình xử lý một hợp đồng?

**A17** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### After round 3 (interviewer notes, not answers)

- Three rounds used; no more questions are asked. What is unclear becomes an open question with an `[assumed]` default.
- C1: the need behind the "not ticked" list is stated in A16 (a list of contracts ending within 90 days that are still 有効, opened by 総務担当). A requirement is written for that need; the "not ticked" list is not.
- Whether the checkbox 「更新確認済」 itself is still wanted is not clear: A14 asks for it, A16 says a status will do, A17 does not say who ticks it or when. This needs interpretation, so it is an open question, not a requirement.
- No proposal was made by the AI in this interview (no `P<n>`).

Area coverage at the end:

| Area | State | From |
|---|---|---|
| Data and fields | covered; 担当者 open | A2, A10 |
| Life cycle and statuses | partly — after 更新済, origin states of 解約, 自動更新 open | A3, A4, A8, A9 |
| Roles and permissions | covered | A3, A6 |
| Existing data and migration | covered; PDF files open | A12 |
| Notifications and reminders | covered; other exclusions open | A7, A11 |
| Validation rules | covered | A2, A13 |
| Lists and reports | covered; checkbox and export open | A14, A16, A17 |
| Volume and deadline | covered | A12, A15 |

## Summary for confirmation

Sent 2026-11-11, in Vietnamese, as below.

**Hệ thống dùng để làm gì**

Bên tổng vụ (総務部) đang theo dõi hợp đồng với nhà cung cấp bằng Excel và hay bị quên gia hạn. Họ muốn đưa lên Pleasanter để quản lý và được nhắc trước khi hợp đồng hết hạn.

**Những điểm chị đã trả lời**

1. Dữ liệu
   - Một bản ghi là một hợp đồng với một nhà cung cấp (取引先). (A2)
   - Các mục: 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yên), 担当者, 担当部門, file PDF hợp đồng đính kèm. (A2)
   - Bắt buộc: 契約名, 取引先, 契約終了日, 担当者. (A2)
2. Các giai đoạn
   - 有効 → 更新検討中 → 更新済 hoặc 解約. (A3)
   - 総務担当 chuyển sang 更新検討中 và sang 更新済. (A3)
   - Chỉ 総務課長 được chuyển sang 解約. (A3, A6, A9)
   - Hợp đồng đã 解約 thì không mở lại. (A3)
3. Người dùng và quyền
   - 総務担当 (3 người): tạo và sửa tất cả hợp đồng. (A6)
   - 総務課長 (1 người): xem tất cả. (A6)
   - 各部門の担当者 (khoảng 8 người, 6 phòng ban): chỉ xem hợp đồng của 担当部門 mình, không sửa. (A6)
4. Dữ liệu hiện có
   - File Excel có khoảng 180 hợp đồng; khoảng 140 hợp đồng còn hiệu lực phải có trong hệ thống ngay ngày đầu; hợp đồng cũ đã 解約 thì không cần. (A12)
5. Lời nhắc
   - Gửi mail cho 担当者 trước 契約終了日 60 ngày. (A7)
   - Đến 30 ngày trước 契約終了日 mà hợp đồng vẫn còn 有効 thì gửi thêm mail cho 総務課長. (A7)
   - Hợp đồng 解約 thì không gửi gì. (A7, A11)
   - Lời nhắc trong kênh Microsoft Teams của 総務部: mong muốn, không bắt buộc, có thể làm sau. (A7, A15)
6. Quy tắc nhập
   - 契約終了日 phải sau 契約開始日. (A13)
   - 月額 phải là số nguyên yên, từ 0 trở lên. (A13)
7. Danh sách
   - Các hợp đồng sắp hết hạn trong 90 ngày, sắp xếp theo 契約終了日. (A14)
   - Tổng 月額 theo từng 取引先; có thể làm sau nếu cần. (A14, A15)
   - Danh sách cho 総務担当: mọi hợp đồng sẽ hết hạn trong 90 ngày tới mà vẫn chưa được chuyển khỏi trạng thái 有効. (A16)
8. Khối lượng và thời hạn
   - Khoảng 15 hợp đồng mới mỗi tháng, tổng cộng 12 người dùng. (A15)
   - Hệ thống phải dùng được trước 2027-04-01. (A12, A15)

**Đề xuất của em mà chị đã chấp nhận:** không có (em không đưa ra đề xuất nào).

**Giới hạn**

- C1: danh sách "các hợp đồng chưa được tick 更新確認済" không làm được, vì Pleasanter chỉ lọc được theo "đã tick" (mục D9, đã kiểm chứng trên bản 1.5.2). Nhu cầu chị nêu thay cho nó là danh sách ở mục 7, dòng thứ ba (A16).

**Cần kiểm chứng ở bước thiết kế (em chưa hứa là làm được)**

- Gửi mail theo số ngày trước 契約終了日 (60 và 30 ngày). (A7)
- Lời nhắc trong kênh Microsoft Teams. (A7)
- 各部門の担当者 chỉ thấy hợp đồng của 担当部門 mình. (A6)
- Danh sách lọc theo "hết hạn trong 90 ngày". (A14, A16)
- Tổng 月額 theo từng 取引先. (A14)
- Từ chối 月額 không phải số nguyên hoặc nhỏ hơn 0. (A13)

**Còn mở — chưa được thống nhất.** Nếu chưa có câu trả lời, em sẽ ghi thành câu hỏi cho khách kèm giả định dưới đây; giả định chỉ là tạm, không phải điều chị đã đồng ý.

| # | Điểm còn mở | Giả định tạm |
|---|---|---|
| a | 担当者 trên hợp đồng là ai (A10) | chọn được bất kỳ người dùng nào của hệ thống |
| b | Sau 更新済, kỳ hợp đồng tiếp theo được theo dõi thế nào (A8) | 更新済 là giai đoạn cuối của bản ghi đó; kỳ tiếp theo được nhập thành hợp đồng mới |
| c | 解約 được làm từ giai đoạn nào (A9) | từ 有効 và 更新検討中 |
| d | Hợp đồng 自動更新 xử lý thế nào (A4) | xử lý như hợp đồng khác, vẫn nhận lời nhắc |
| e | Mail 60 ngày còn trường hợp nào không gửi ngoài 解約 (A11) | chỉ 解約 là không gửi |
| f | File PDF có đưa sang hệ thống mới không (A12) | không đưa sang ngày đầu; đính kèm dần bằng tay |
| g | Có cần xuất danh sách ra file không (A14) | không cần |
| h | Checkbox 「更新確認済」 có còn cần không, ai tick, lúc nào (A14, A16, A17) | không làm checkbox; dùng danh sách theo trạng thái ở A16 |
| i | Danh sách tổng 月額 và phần Teams làm ngay hay để sau (A15) | để sau, không nằm trong đợt đầu |
| j | Cách dùng file Excel hiện nay; cách xử lý khi sắp hết hạn; ví dụ quên gia hạn; ví dụ nhập sai (A1, A4, A5, A13) | không có giả định; chỉ là thông tin tham khảo |

**Confirmation** (Lan):

> Chỗ "hay bị quên gia hạn" chị chưa nói vậy, em bỏ ra giúp chị. Chị chưa kể lần nào bị quên cả. Phần mô tả mục đích em chỉ nên ghi là bên tổng vụ theo dõi hợp đồng bằng Excel và muốn được nhắc trước khi hợp đồng hết hạn.
>
> Đúng rồi em, chị xác nhận phần còn lại.
>
> Mấy điểm còn mở thì đúng là chưa chốt, chị sẽ hỏi lại.
>
> Phê duyệt thì để anh Nam quyết, chị chỉ xác nhận nội dung thôi.

### A18 — correction (corrects the purpose paragraph of the summary)

**A18** (Lan): Chỗ "hay bị quên gia hạn" chị chưa nói vậy, em bỏ ra giúp chị. Chị chưa kể lần nào bị quên cả. Phần mô tả mục đích em chỉ nên ghi là bên tổng vụ theo dõi hợp đồng bằng Excel và muốn được nhắc trước khi hợp đồng hết hạn.

### After the confirmation (interviewer notes, not answers)

- Purpose as corrected by A18: 総務部 tracks contracts in Excel and wants to be reminded before a contract expires. "hay bị quên gia hạn" is not used as a fact anywhere in the requirements. The idea at the top of this record stays as it was received (the record is never tidied up); the words appear there, and the person withdrew them in A18.
- The rest of the summary is confirmed as a correct report of the interview. The confirmation accepts no proposal and settles no open point: points a–j stay open (the person said so herself).
- The confirmation is not G1. The person named Nam as the one who decides on approval, which matches the project profile (G1 approver: Nam).

