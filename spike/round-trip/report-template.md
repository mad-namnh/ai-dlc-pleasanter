# Báo cáo spike round-trip — YYYY-MM-DD

> Báo cáo này được commit vào repo framework → **đã làm sạch**: không tên site, tên người, URL nội bộ, giá trị cấu hình của khách.

## Môi trường

- Pleasanter: 1.5.__.__ (bản patch chính xác)
- PostgreSQL: __
- Nguồn cấu hình: site mẫu tự tạo / bản sao cấu hình khách (môi trường: __)

## Kết quả theo câu hỏi

| Câu hỏi | Kết quả | Bằng chứng |
|---|---|---|
| 1. Round-trip giống hệt (create) | | `data/local/roundtrip-create/report.md` |
| 1. Round-trip giống hệt (update) | | `data/local/roundtrip-update/report.md` |
| 2. Thành phần phải làm tay | | `inventory-checklist.md` |
| 3. Idempotent | | report update, cặp "lần 2 vs lần 1" |
| 4. Trường chứa secret | | output `scan_secrets.py` (chỉ path) |

## Xác nhận endpoint (Bước 0)

| Thao tác | Endpoint 1.5.x | Cấu trúc response | Ghi chú |
|---|---|---|---|
| Lấy site | | | |
| Tạo site | | | |
| Cập nhật site | | | |

## Site package vs API

- Site package giữ được mà API không: 
- API giữ được mà site package không: 

## MCP tích hợp (nếu đã thử)

- Tool có sẵn: 
- Dùng được cho framework: 

## Phát hiện mới → review-findings

| ID mới | Mức | Nội dung |
|---|---|---|
| | | |

## Quyết định

**Go / Đổi hướng / No-go** — lý do:

Cập nhật tiếp: ADR-0001 (phạm vi), ADR-0004 (danh sách thay đổi ảnh hưởng dữ liệu), ADR-0005 (trường chứa secret).
