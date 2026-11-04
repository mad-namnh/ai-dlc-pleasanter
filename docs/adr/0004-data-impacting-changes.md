# ADR-0004: Change có ảnh hưởng dữ liệu và gate riêng

- **Trạng thái:** Đề xuất
- **Ngày:** 2026-11-04
- **Liên quan:** review-findings A1, ADR-0001, ADR-0002

## Bối cảnh

Trên site đã có dữ liệu, một số thay đổi cấu hình thực chất là thay đổi schema. Cấu hình rollback được bằng snapshot, dữ liệu thì không. Cần phân loại tự động và gate riêng cho loại rủi ro.

## Câu hỏi mở

- [ ] Danh sách thay đổi cấu hình nào làm ảnh hưởng dữ liệu hiện có trên 1.5.x (đổi kiểu hiển thị, đổi lựa chọn, đổi công thức, đổi validation, đổi ứng xử khi xóa…) — *Spike*
- [ ] Giới hạn của API bulk upsert (số lượng, hiệu năng, lịch sử phiên bản) — *Spike*
- [ ] Khách yêu cầu backup DB trước change loại này không — *IT khách*

## Phân loại đề xuất

| Loại | Ví dụ | Gate |
|---|---|---|
| **Chỉ cấu hình** | Đổi nhãn, thứ tự, view, thông báo, style | Gate thường |
| **Ảnh hưởng dữ liệu** | Tái sử dụng / đổi nghĩa ô cột, gỡ cột đang có dữ liệu, đổi lựa chọn đang được dùng, đổi công thức tính lại giá trị, đổi quy trình làm trạng thái cũ không hợp lệ | Gate riêng: script migration + dry-run trên bản sao dữ liệu + kế hoạch rollback + người duyệt nghiệp vụ phía khách |
| **Ảnh hưởng quyền** | Đổi quyền site/record/cột | Gate riêng: ma trận quyền trước/sau |

## Các phương án

### Phương án A — Phân loại bằng quy tắc tĩnh trên diff
- Ưu: tất định, giải thích được
- Nhược: phải bảo trì danh sách quy tắc

### Phương án B — Quy tắc tĩnh + truy vấn production xem ô có dữ liệu không
- Ưu: chính xác hơn (gỡ cột trống ≠ gỡ cột có dữ liệu)
- Nhược: cần quyền đọc production (qua runner/người vận hành)

## Quyết định

*(Chưa chốt)* — Đề xuất **A trước, B khi có runner** (ADR-0003).

## Hệ quả

- CLI cần lệnh phân loại change, chạy trong CI, kết quả hiện trong báo cáo diff.
- Mỗi change loại "ảnh hưởng dữ liệu" có thư mục migration: script, dry-run log, rollback.
