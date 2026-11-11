# Interview — vendor contract management for 総務部

- **Person:** Lan, project coordinator for the customer's 総務部 · **Interviewer:** AI (pls-p1-requirements-analyst) · **Date:** 2026-11-11 · **Language:** Vietnamese

## The idea (verbatim)

> Bên tổng vụ (総務部) của khách đang theo dõi hợp đồng với nhà cung cấp bằng Excel, hay bị quên gia hạn. Họ muốn đưa lên Pleasanter để quản lý và được nhắc trước khi hợp đồng hết hạn. Em làm giúp chị nhé.

Why interview mode: the idea names a goal only. It does not say what one record is and its fields, the states a record goes through, or who may do what.

Repository state before the first question: `config/` and `design/` are empty, `requirements/index.md` has no requirement and no question, `environments.json` has `dev` only with no sites. Nothing in the repository answers a question.

Note sent to the person with round 1 (knowledge base check): the knowledge base has entries on mail notifications sent when a record changes (schema: `Notifications[]`), but no entry on a reminder sent a set time before a date. The wish "được nhắc trước khi hợp đồng hết hạn" is therefore recorded as asked and marked `[unverified]`: not promised, to be verified in P2.

## Round 1

### Q1
Hiện nay bên 総務部 theo dõi một hợp đồng trong Excel như thế nào, từng bước một — từ lúc ký hợp đồng cho đến lúc hợp đồng kết thúc hoặc được gia hạn?

**A1** (Lan): Chị chỉ biết là họ theo dõi hợp đồng trong Excel và hay quên gia hạn. Từng bước chi tiết thì chị không rõ, để chị hỏi lại bên tổng vụ.

### Q2
Một dòng trong file Excel đó là gì, và họ ghi những thông tin nào cho mỗi dòng? Trong đó thông tin nào lúc nào cũng phải có?

**A2** (Lan): Một dòng là một hợp đồng với nhà cung cấp (取引先). Các cột họ ghi: 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yên), 担当者, 担当部門, và file PDF hợp đồng đính kèm. Bắt buộc phải có: 契約名, 取引先, 契約終了日, 担当者.

### Q3
Từ lúc được nhập vào cho đến lúc không cần theo dõi nữa, một hợp đồng đi qua những trạng thái nào? Ai là người chuyển trạng thái, và điều gì thì kết thúc việc theo dõi một hợp đồng?

**A3** (Lan): Trạng thái: 有効 → 更新検討中 → 更新済 hoặc 解約. 総務担当 chuyển sang 更新検討中 và 更新済. Chuyển sang 解約 thì chỉ 総務課長 được làm. Hợp đồng đã 解約 thì không mở lại nữa. Còn hợp đồng 自動更新 đến ngày kết thúc thì xử lý thế nào, chị chưa rõ, để chị hỏi lại.

### Q4
Khi một hợp đồng được gia hạn, hôm nay họ làm gì với dòng đó trong Excel?

**A4** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q5
Những ai sẽ làm việc với dữ liệu hợp đồng: ai nhập mới, ai sửa, ai chỉ xem, và có ai không được phép thấy không?

**A5** (Lan): 総務担当 (3 người): tạo mới và sửa tất cả hợp đồng. 総務課長 (1 người): xem tất cả, và chỉ người này được chuyển sang 解約. 各部門の担当者 (khoảng 8 người ở 6 phòng ban): chỉ xem hợp đồng thuộc 担当部門 của mình, không sửa gì.

### Q6
Về việc nhắc trước khi hết hạn: ai cần được biết, cần biết vào lúc nào, và hôm nay họ biết bằng cách nào?

**A6** (Lan): Gửi mail cho 担当者 trước 契約終了日 60 ngày. Nếu 30 ngày trước 契約終了日 mà hợp đồng vẫn còn 有効 thì gửi thêm mail cho 総務課長. Hợp đồng 解約 thì không gửi gì. Chị cũng muốn nhắc hiện luôn trên kênh Microsoft Teams của 総務部, nếu làm được thì tốt, không bắt buộc. Hôm nay họ biết bằng cách nào thì chị không rõ, để chị hỏi lại.

### Q7
Dữ liệu trong file Excel hiện tại: khoảng bao nhiêu hợp đồng, có cần đưa sang Pleasanter không, và nếu có thì cần xong trước khi nào?

**A7** (Lan): Khoảng 180 hợp đồng trong một file Excel. Khoảng 140 cái còn hiệu lực thì phải có trong app ngay ngày đầu, mấy hợp đồng cũ đã kết thúc thì không cần. Mỗi tháng có khoảng 15 hợp đồng mới, tổng 12 người dùng. Phải chạy được trước năm tài chính mới, 2027-04-01. Phần Teams và phần tổng 月額 theo 取引先 thì để sau cũng được nếu gấp.

Note (unprompted, inside A7): a new wish, "tổng 月額 theo 取引先", appears here for the first time; no question had asked for it.

## Coverage after round 1

| Area | State | Basis / what is open |
|---|---|---|
| Data and fields | covered | A2. Open detail: who a 担当者 is (Q8) |
| Life cycle and statuses | partly | A3. Not known to Lan (she will ask 総務部): how renewal is handled today (A1, A4), what happens to a 自動更新 contract at its end date (A3). Not yet asked: from which status 解約 is allowed (Q11), what follows 更新済 (Q10) |
| Roles and permissions | covered | A5 (delete rights and whether 総務課長 edits were not stated) |
| Existing data and migration | covered | A7 |
| Notifications and reminders | partly | A6. Open: which statuses receive the 60-day and 30-day mails (Q9); content of the Teams message (Q15); how people learn of it today (Lan will ask) |
| Validation rules | open | not asked yet (Q12) |
| Lists and reports | open | not asked yet (Q13); total of 月額 per 取引先 raised unprompted in A7 (Q14) |
| Volume and deadline | covered | A7 |

Knowledge base check on the answers of round 1 (told to the person with round 2):

- Reminder mails a set number of days before 契約終了日 (A6): no KB entry → `[unverified]`.
- Message on a Microsoft Teams channel (A6): the KB knows notification type mail only; no entry on Teams → `[unverified]`; the person called it optional.
- 各部門の担当者 see only the contracts of their own 担当部門 (A5): the KB covers permissions per site (D15, D19) and per process (D20); no entry on limiting which records of one site a user can see → `[unverified]`.
- No answer asked for something a KB entry says Pleasanter cannot do: no constraint recorded.

## Round 2

### Q8
担当者 của một hợp đồng là ai — người thuộc nhóm nào trong ba nhóm chị nêu ở câu 5 (総務担当, 総務課長, 各部門の担当者), hay là người khác?

**A8** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q9
Về hai mail nhắc ở câu 6: nếu đến mốc 60 ngày mà hợp đồng đã ở 更新検討中 hoặc 更新済 thì có gửi mail cho 担当者 không? Và ở mốc 30 ngày, nếu hợp đồng đang ở 更新検討中 (không còn 有効) thì 総務課長 có nhận mail không?

**A9** (Lan): Chị chỉ biết: gửi mail cho 担当者 trước 契約終了日 60 ngày, và nếu 30 ngày trước mà hợp đồng vẫn còn 有効 thì gửi thêm cho 総務課長. Hợp đồng 解約 thì không gửi gì. Còn các trường hợp em hỏi (đã sang 更新検討中 hoặc 更新済) thì chị không rõ, để chị hỏi lại bên tổng vụ.

### Q10
Một hợp đồng đã chuyển sang 更新済 thì sau đó còn ai làm gì với nó nữa không?

**A10** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

### Q11
総務課長 được chuyển hợp đồng sang 解約 từ trạng thái nào: (a) chỉ từ 更新検討中, (b) từ 有効 và 更新検討中, (c) từ bất kỳ trạng thái nào, hay (d) cách khác?

**A11** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ. Chị chỉ biết là chỉ 総務課長 được chuyển sang 解約, và 解約 rồi thì không mở lại.

### Q12
Khi 総務担当 nhập mới hoặc sửa một hợp đồng, có trường hợp nào hệ thống phải từ chối không cho lưu không (ngoài việc thiếu bốn thông tin bắt buộc ở câu 2)? Nếu có, chị cho em một ví dụ.

**A12** (Lan): Có hai quy tắc: 契約終了日 phải sau 契約開始日, và 月額 là số nguyên yên, từ 0 trở lên.

### Q13
Hằng ngày mỗi nhóm người dùng sẽ mở danh sách hợp đồng để xem những gì — họ cần lọc, sắp xếp theo gì, và có cần xuất ra file không?

**A13** (Lan): Chị muốn có một checkbox 「更新確認済」 trên mỗi hợp đồng, và một danh sách các hợp đồng chưa được tick. Ngoài ra có danh sách hợp đồng kết thúc trong 90 ngày, sắp xếp theo 契約終了日, và tổng 月額 theo 取引先. Còn lọc theo gì khác hay xuất file thì chị không rõ, để chị hỏi lại bên tổng vụ.

### Q14
Phần tổng 月額 theo 取引先 chị nhắc ở câu 7: ai cần xem con số này, và họ dùng nó để làm gì?

**A14** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ. Chỉ biết là phần này làm sau cũng được nếu gấp.

### Q15
Phần nhắc trên kênh Microsoft Teams của 総務部: chị muốn kênh đó hiện những gì và vào lúc nào?

**A15** (Lan): Chị chỉ muốn nhắc (reminder) hiện trên kênh Teams của 総務部, nếu làm được thì tốt, không bắt buộc. Hiện những gì và vào lúc nào thì chị không rõ, để chị hỏi lại bên tổng vụ.

## Coverage after round 2

| Area | State | Basis / what is open |
|---|---|---|
| Data and fields | covered | A2, A13 (checkbox 「更新確認済」). Not known to Lan: who a 担当者 is (A8) |
| Life cycle and statuses | partly | A3, A11. Not known to Lan: renewal handling (A4), 自動更新 at the end date (A3), what follows 更新済 (A10), from which status 解約 is allowed (A11) |
| Roles and permissions | covered | A5. Not stated: who ticks 「更新確認済」 (Q17); delete rights; whether 総務課長 edits |
| Existing data and migration | covered | A7 |
| Notifications and reminders | partly | A6, A9. Not known to Lan: mails for 更新検討中 / 更新済 (A9); Teams content and timing (A15) |
| Validation rules | covered | A12 |
| Lists and reports | partly | A13. Constraint C1 on the "not ticked" list (Q16). Not known to Lan: other filters, export (A13); who uses the total of 月額 per 取引先 and for what (A14) |
| Volume and deadline | covered | A7 |

Knowledge base check on the answers of round 2 (told to the person with round 3):

- List of contracts whose 「更新確認済」 checkbox is **not** ticked (A13): KB D9 (1.5.2) — a checkbox list filter is 2-state, it can select "checked" but not "unchecked" → constraint C1 below.
- List of contracts ending within 90 days, sorted by 契約終了日 (A13): the KB has the view sorter and the Issues `Overdue` filter (D24) only; no entry on a filter "date within the next N days" → `[unverified]`.
- Total of 月額 per 取引先 (A7, A13): the KB has totals written to a linked parent record (D16, D23). Whether 取引先 is a record of its own is a design matter for P2; nothing here is promised beyond D16.
- 契約終了日 after 契約開始日 (A12): KB D25 — no built-in check, a refusal needs a script. 月額 a whole number ≥ 0 (A12): no KB entry on numeric input limits → `[unverified]`. Required fields (A2): KB D27 — required is enforced on the screen only.

## Round 3

### C1 — constraint (KB D9)
Asked for (A13): "một danh sách các hợp đồng chưa được tick" for the checkbox 「更新確認済」. Pleasanter 1.5.2 cannot filter a list on "checkbox not ticked" (KB D9: checkbox filters are 2-state, only "checked"). Told to the person with round 3. What the person needs instead — their words: see A16.

### Q16
Danh sách "các hợp đồng chưa được tick 「更新確認済」" ở câu 13: theo tài liệu kiểm chứng của bên em (mục D9, Pleasanter 1.5.2), Pleasanter chỉ lọc được danh sách theo checkbox "đã tick", không lọc được theo "chưa tick", nên em không thể đưa danh sách đúng dạng đó vào yêu cầu. Danh sách ấy sẽ giúp bên tổng vụ làm được việc gì — họ mở nó ra để biết điều gì, rồi làm gì tiếp?

**A16** (Lan): 総務担当 muốn thấy mọi hợp đồng kết thúc trong vòng 90 ngày mà vẫn chưa chuyển khỏi trạng thái 有効. Dùng trạng thái cũng được, miễn là thấy được danh sách đó.

### Q17
Checkbox 「更新確認済」: ai là người tick, và tick vào lúc nào?

**A17** (Lan): Cái này chị không rõ, để chị hỏi lại bên tổng vụ.

## Coverage after round 3 (interview closed: 3 rounds used)

| Area | State | Basis / what stays open |
|---|---|---|
| Data and fields | covered | A2, A13. Open: who a 担当者 is (A8); whether the checkbox 「更新確認済」 is still wanted after C1 / A16; who ticks it and when (A17) |
| Life cycle and statuses | partly | A3, A11. Open: renewal handling (A4), 自動更新 at the end date (A3), what follows 更新済 (A10), from which status 解約 is allowed (A11) |
| Roles and permissions | covered | A5. Open: delete rights; whether 総務課長 edits |
| Existing data and migration | covered | A7. Open: status of the migrated contracts |
| Notifications and reminders | partly | A6, A9. Open: mails for 更新検討中 / 更新済 (A9); Teams content and timing (A15) |
| Validation rules | covered | A12 |
| Lists and reports | partly | A13, A16 (need behind C1). Open: other filters, export (A13); total of 月額 per 取引先 — who and what for (A14) |
| Volume and deadline | covered | A7 |

No proposal (`P<n>`) was made in this interview.

## Summary for confirmation

Sent to Lan on 2026-11-11, verbatim:

> **Tóm tắt để chị xác nhận hoặc sửa**
>
> **App dùng để làm gì.** Bên tổng vụ (総務部) đang theo dõi hợp đồng với nhà cung cấp bằng Excel và hay bị quên gia hạn. Họ muốn đưa lên Pleasanter để quản lý và được nhắc trước khi hợp đồng hết hạn (ý tưởng ban đầu).
>
> **1. Dữ liệu**
> - Một bản ghi là một hợp đồng với nhà cung cấp (取引先). Các thông tin: 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (yên), 担当者, 担当部門, file PDF hợp đồng đính kèm. Bắt buộc: 契約名, 取引先, 契約終了日, 担当者. (A2)
> - Một checkbox 「更新確認済」 trên mỗi hợp đồng. (A13)
>
> **2. Trạng thái**
> - 有効 → 更新検討中 → 更新済 hoặc 解約. 総務担当 chuyển sang 更新検討中 và 更新済. Chỉ 総務課長 được chuyển sang 解約. Hợp đồng đã 解約 thì không mở lại. (A3, A11)
>
> **3. Người dùng và quyền**
> - 総務担当 (3 người): tạo mới và sửa tất cả hợp đồng. 総務課長 (1 người): xem tất cả, và chỉ người này được chuyển sang 解約. 各部門の担当者 (khoảng 8 người ở 6 phòng ban): chỉ xem hợp đồng thuộc 担当部門 của mình, không sửa gì. (A5)
>
> **4. Dữ liệu hiện có**
> - Khoảng 180 hợp đồng trong một file Excel; khoảng 140 hợp đồng còn hiệu lực phải có trong app ngay ngày đầu; hợp đồng cũ đã kết thúc thì không cần. (A7)
>
> **5. Nhắc**
> - Gửi mail cho 担当者 trước 契約終了日 60 ngày. Nếu 30 ngày trước 契約終了日 mà hợp đồng vẫn còn 有効 thì gửi thêm mail cho 総務課長. Hợp đồng 解約 thì không gửi gì. (A6, A9)
> - Nhắc hiện trên kênh Microsoft Teams của 総務部: nếu làm được thì tốt, không bắt buộc; để sau cũng được nếu gấp. (A6, A7, A15)
>
> **6. Quy tắc nhập**
> - 契約終了日 phải sau 契約開始日. 月額 là số nguyên yên, từ 0 trở lên. (A12)
>
> **7. Danh sách**
> - Danh sách hợp đồng kết thúc trong 90 ngày, sắp xếp theo 契約終了日. (A13)
> - 総務担当 thấy được mọi hợp đồng kết thúc trong vòng 90 ngày mà vẫn chưa chuyển khỏi trạng thái 有効; dùng trạng thái cũng được. (A16 — thay cho danh sách "chưa tick", xem C1)
> - Tổng 月額 theo 取引先; để sau cũng được nếu gấp. (A7, A13)
>
> **8. Khối lượng và thời hạn**
> - Khoảng 15 hợp đồng mới mỗi tháng, tổng 12 người dùng. Phải chạy được trước năm tài chính mới, 2027-04-01. (A7)
>
> **Giới hạn của Pleasanter (C1).** Danh sách "các hợp đồng chưa được tick 「更新確認済」" (A13) không làm được đúng dạng đó: Pleasanter 1.5.2 chỉ lọc được checkbox "đã tick" (mục D9). Nhu cầu chị nêu thay vào đó là danh sách ở mục 7, dòng thứ hai (A16).
>
> **Đề xuất của em.** Em không đưa ra đề xuất nào trong buổi phỏng vấn này.
>
> **Chưa thể hứa chắc — cần kiểm chứng ở bước thiết kế** (vẫn được viết thành yêu cầu, nhưng chưa ai chứng minh Pleasanter làm được):
> - mail nhắc theo số ngày trước 契約終了日 (60 ngày, 30 ngày);
> - nhắc trên kênh Microsoft Teams;
> - 各部門の担当者 chỉ xem được hợp đồng thuộc 担当部門 của mình;
> - danh sách lọc theo "kết thúc trong 90 ngày";
> - quy tắc 月額 là số nguyên từ 0 trở lên.
>
> **Còn mở — chưa được thống nhất.** Đây là các điểm chị nói sẽ hỏi lại bên tổng vụ, hoặc chưa ai nêu. Em ghi kèm giả định em sẽ dùng nếu chưa có câu trả lời; giả định không phải là điều đã thống nhất, và em sẽ không viết yêu cầu từ giả định.
> 1. Khi gia hạn thì làm gì với bản ghi hợp đồng (A4). Giả định: 総務担当 sửa 契約終了日 trên chính bản ghi đó.
> 2. Hợp đồng 自動更新 đến ngày kết thúc thì xử lý thế nào (A3). Giả định: hệ thống không tự làm gì; hợp đồng 自動更新 được nhắc và theo dõi như mọi hợp đồng khác.
> 3. Hợp đồng đã 更新済 thì sau đó còn ai làm gì nữa không (A10). Giả định: không; 更新済 không chuyển tiếp sang trạng thái nào khác.
> 4. 総務課長 chuyển sang 解約 từ trạng thái nào (A11). Giả định: chỉ từ 更新検討中, theo đúng thứ tự chị nêu ở câu 3.
> 5. 担当者 của hợp đồng là ai (A8). Giả định: một người dùng Pleasanter có địa chỉ mail, thuộc nhóm nào cũng được.
> 6. Mail 60 ngày có gửi khi hợp đồng đã ở 更新検討中 hoặc 更新済 không; mail 30 ngày có gửi cho 総務課長 khi hợp đồng ở 更新検討中 không (A9). Giả định: mail 60 ngày gửi cho mọi hợp đồng trừ 解約; mail 30 ngày chỉ gửi khi còn 有効 — đúng theo chữ ở câu 6.
> 7. Kênh Teams hiện những gì, vào lúc nào (A15). Giả định: cùng nội dung và cùng lúc với mail 60 ngày; làm sau đợt đầu.
> 8. Tổng 月額 theo 取引先: ai xem, dùng để làm gì (A14). Giả định: 総務担当 và 総務課長 xem; tính trên các hợp đồng chưa 解約; làm sau đợt đầu.
> 9. Lọc theo gì khác, có xuất file không (A13). Giả định: không có gì thêm.
> 10. Ai tick 「更新確認済」, tick lúc nào (A17). Giả định: 総務担当, bất cứ lúc nào.
> 11. Sau khi đã có danh sách theo trạng thái (A16), checkbox 「更新確認済」 có còn cần không. Giả định: vẫn cần, vì chị đã yêu cầu ở câu 13.
> 12. Có ai được xoá hợp đồng không; 総務課長 có sửa nội dung hợp đồng không (chưa ai nêu). Giả định: không ai xoá; 総務課長 chỉ xem và chuyển sang 解約.
> 13. Hợp đồng đang 更新検討中 có được chuyển ngược về 有効 không (chưa ai nêu). Giả định: không.
> 14. 140 hợp đồng đưa sang lúc đầu ở trạng thái nào (chưa ai nêu). Giả định: tất cả là 有効.
> 15. Hợp đồng không ghi 担当部門 thì 各部門の担当者 nào xem được (chưa ai nêu). Giả định: không ai trong nhóm đó xem được.
>
> Chị xem giúp em bản tóm tắt này đã ghi đúng những gì chị nói chưa; nếu có chỗ sai hoặc thiếu chị sửa giúp em. Việc chị xác nhận chỉ có nghĩa là em đã hiểu đúng lời chị — không có nghĩa là các điểm "còn mở" đã được chốt, và cũng chưa phải là duyệt yêu cầu (việc duyệt làm sau, trên từng file yêu cầu).

**Confirmation** (Lan): Đúng rồi em, chị xác nhận. Mấy điểm còn mở thì đúng là chưa chốt, chị sẽ hỏi lại.

Note: the confirmation says the summary reports the interview correctly. It accepts no proposal (none was made), settles none of the 15 open points, and is not gate G1.
