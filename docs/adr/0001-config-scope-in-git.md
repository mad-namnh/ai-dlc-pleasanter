# ADR-0001: Phạm vi cấu hình được quản lý trong git

- **Trạng thái:** Đề xuất
- **Ngày:** 2026-11-04
- **Liên quan:** review-findings B4, ADR-0004, ADR-0005

## Bối cảnh

Chính bản của dự án Pleasanter là cấu hình nằm trong DB. Framework chỉ kiểm soát được những gì xuất ra file và đưa vào lại được một cách tin cậy. Ở 1.5.x, schema SiteSettings không được tài liệu hóa đầy đủ từng trường. Phạm vi phải dựa trên **kết quả spike round-trip**, không dựa trên giả định.

## Câu hỏi mở

- [ ] Những thành phần nào round-trip được 100% qua API site (xem `spike/round-trip/inventory-checklist.md`)? — *Spike*
- [ ] Site package export/import có giữ được những gì API site không giữ không? — *Spike*
- [ ] File trên server (thư mục `Parameters/`, extended SQL, …) có được đưa vào quản lý không, ai có quyền đọc/ghi? — *IT khách*
- [ ] User / group / dept: quản lý trong git hay coi là dữ liệu tham chiếu do khách quản lý? — *Khách*
- [ ] Dashboard, trang tổng hợp, thiết lập cấp tenant có round-trip được không? — *Spike*

## Các phương án

### Phương án A — Chỉ quản lý những gì round-trip 100%
- Ưu: an toàn, git luôn phản ánh đúng thực tế
- Nhược: phần còn lại phải làm tay, có thể lớn

### Phương án B — Quản lý cả phần round-trip một phần, kèm runbook thao tác tay
- Ưu: phủ rộng hơn, có tài liệu cho mọi thứ
- Nhược: git có thể lệch thực tế ở phần làm tay; cần kiểm tra sau deploy

### Phương án C — Bổ sung đọc/ghi trực tiếp DB cho phần API không phủ
- Ưu: phủ gần như toàn bộ
- Nhược: rủi ro cao, phụ thuộc cấu trúc DB nội bộ, khó qua kiểm duyệt của khách và khi nâng cấp phiên bản

## Quyết định

*(Chưa chốt — chờ spike)*

Đề xuất ban đầu: **B**, với điều kiện phần làm tay < ~20% số thành phần theo checklist và không chứa thành phần rủi ro cao (quyền, quy trình). Không chọn C trừ khi có lý do rất mạnh.

## Hệ quả

- Danh sách "trong phạm vi" trở thành đầu vào cho CLI unpack/pack và JSON schema validate.
- Phần ngoài phạm vi phải có runbook và bước kiểm tra sau deploy.
