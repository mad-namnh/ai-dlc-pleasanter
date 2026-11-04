# ADR-0005: Chính sách lưu cấu hình và secret

- **Trạng thái:** Đề xuất
- **Ngày:** 2026-11-04
- **Liên quan:** review-findings B1, C4

## Bối cảnh

Dự án on-prem; một phần đội ngũ làm việc từ Việt Nam. Cấu hình có thể chứa thông tin nhạy cảm: webhook URL của thông báo, token/URL trong server script, địa chỉ mail, tên người/phòng ban trong quyền, hostname nội bộ. Dữ liệu nghiệp vụ gần như chắc chắn không được rời mạng khách.

## Câu hỏi mở

- [ ] Khách có cho phép cấu hình (không kèm dữ liệu) nằm trong git do MADLAB quản lý không? Ở đâu (GitHub org MADLAB / Git server của khách)? — *Hợp đồng/khách*
- [ ] Thành viên tại Việt Nam được xem cấu hình đến mức nào? — *Hợp đồng/khách*
- [ ] Những trường nào trong SiteSettings 1.5.x có thể chứa secret — *Spike (quét mẫu export)*

## Các phương án

### Phương án A — Repo dự án trên Git server của khách
- Ưu: dữ liệu không rời khách, dễ duyệt
- Nhược: MADLAB phụ thuộc hạ tầng/quyền truy cập của khách

### Phương án B — Repo dự án trong GitHub org của MADLAB, cấu hình đã làm sạch secret
- Ưu: vận hành thuận tiện, CI/agent dễ dùng
- Nhược: cần khách đồng ý bằng văn bản; phải chứng minh quét secret hiệu quả

## Quyết định

*(Chưa chốt)*

Bất kể phương án nào, các nguyên tắc sau là **bắt buộc**:
1. Secret không bao giờ vào git: khi unpack, thay bằng tham chiếu `${SECRET_NAME}`; giá trị nằm ở kho secret của từng môi trường.
2. Quét secret là bước CI bắt buộc (chặn merge nếu phát hiện).
3. Dữ liệu nghiệp vụ không rời mạng khách; test dùng dữ liệu tổng hợp.
4. Báo cáo/ví dụ đưa vào repo framework phải được làm sạch.

## Hệ quả

- CLI unpack cần bộ quét + thay thế secret; pack cần bước nạp lại secret theo môi trường.
- Cần danh mục secret theo môi trường trong repo dự án (chỉ tên, không giá trị).
