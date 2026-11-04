# ADR-0002: Dải ô cột theo vùng sở hữu

- **Trạng thái:** Đề xuất
- **Ngày:** 2026-11-04
- **Liên quan:** review-findings A2, B2

## Bối cảnh

Cột trong Pleasanter là ô có kiểu cố định (Class*, Num*, Date*, Description*, Check*, Attachments*…). Khách có thể tự thêm cột trên UI. Nếu khách và framework cùng cấp một ô trên cùng site, hai trường sẽ đè lên nhau kèm dữ liệu thật.

"Vùng sở hữu" không thể thực thi hoàn toàn bằng phân quyền vì admin phía khách vẫn sửa được mọi nơi. Thực thi thật là **phát hiện drift + kiểm tra xung đột ô trước deploy**, cộng thỏa thuận bằng văn bản.

## Câu hỏi mở

- [ ] Số ô mỗi loại khả dụng trên 1.5.x, và cột mở rộng (拡張項目) hoạt động thế nào — *Spike / manual*
- [ ] Khách có đồng ý chia dải ô và ghi vào hợp đồng/SLA bảo trì không — *Khách*
- [ ] Site do khách tự tạo hoàn toàn: framework có theo dõi không — *Khách*

## Các phương án

### Phương án A — Chia dải ô cố định theo vùng
Ví dụ: MADLAB dùng A–M, khách dùng N trở đi (mỗi loại ô).
- Ưu: đơn giản, dễ kiểm tra tự động, dễ giải thích với khách
- Nhược: lãng phí ô; site cũ đã dùng ô lộn xộn phải lập bảng ngoại lệ

### Phương án B — Khách chỉ dùng cột mở rộng
- Ưu: không đụng dải ô chuẩn
- Nhược: phụ thuộc giới hạn của cột mở rộng; khách phải học cách khác

### Phương án C — Không chia dải, chỉ khóa ô bằng sổ cấp phát + kiểm tra trước deploy
- Ưu: linh hoạt
- Nhược: xung đột chỉ phát hiện lúc deploy, phải hòa giải thủ công thường xuyên

## Quyết định

*(Chưa chốt)*

Đề xuất ban đầu: **A cho site mới, C cho site hiện hữu** (sổ cấp phát ghi nhận hiện trạng, ô trống mới cấp theo dải).

## Hệ quả

- Cần **sổ cấp phát ô cột** trong repo dự án: `site → ô → tên logic → vùng → trạng thái`.
- Kiểm tra trước deploy: diff ô giữa production và git; ô bị chiếm ngoài sổ → chặn deploy.
- Báo cáo drift định kỳ gửi khách kiêm bằng chứng khi tranh chấp.
