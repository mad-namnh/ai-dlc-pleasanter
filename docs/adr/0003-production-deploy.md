# ADR-0003: Cách deploy lên production (on-prem)

- **Trạng thái:** Đề xuất
- **Ngày:** 2026-11-04
- **Liên quan:** review-findings A3, B1, D1

## Bối cảnh

Production nằm trong mạng on-prem của khách. API key quản trị tenant rất mạnh. Hook của agent không phải ranh giới bảo mật. Nguyên tắc cứng: **AI không bao giờ giữ key production, không có đường mạng tới production.**

## Câu hỏi mở

- [ ] Khách cho phép runner tự động chạy trong mạng của họ không? Ở đâu (máy chủ, VM, GitHub self-hosted runner…)? — *IT khách*
- [ ] Có môi trường staging on-prem không? Cấu hình có giống production không? — *IT khách*
- [ ] Ai được phát hành API key, quyền tối thiểu cần thiết cho deploy cấu hình là gì? — *Spike + IT khách*
- [ ] Khung giờ được phép deploy, quy trình thông báo người dùng — *Khách*
- [ ] Có dùng MCP tích hợp của Pleasanter ở môi trường nào không (D1)? — *Khách*

## Các phương án

### Phương án A — Runner trong mạng khách, deploy tự động sau G4
- Ưu: nhanh, lặp lại được, có log đầy đủ
- Nhược: cần IT khách duyệt hạ tầng; phải bảo vệ runner

### Phương án B — Gói deploy + người vận hành phía khách import tay
Framework xuất "gói deploy" (cấu hình đã pack + deploy plan + checklist + script kiểm tra sau deploy).
- Ưu: dễ được khách chấp nhận, không cần hạ tầng mới
- Nhược: chậm, phụ thuộc người, dễ sai bước

### Phương án C — Bắt đầu B, chuyển dần sang A
- Ưu: khởi động được ngay, xây lòng tin trước
- Nhược: phải duy trì hai luồng trong giai đoạn chuyển tiếp

## Quyết định

*(Chưa chốt)*

Đề xuất ban đầu: **C**. Gói deploy được thiết kế sao cho chính runner ở phương án A cũng dùng nguyên gói đó.

## Hệ quả

- Mọi deploy đều đi qua **deploy plan** (A3): snapshot → thứ tự phụ thuộc → áp → smoke test → khôi phục nếu lỗi.
- Môi trường làm việc của AI (local/CI của MADLAB) không có route tới mạng khách — thực thi ở tầng mạng.
- Audit log: ai duyệt, ai chạy, bản nào, lúc nào.
