# Spike B4 — Round-trip cấu hình Pleasanter 1.5.x

## Câu hỏi cần trả lời

1. Cấu hình site export qua API/site package → đưa vào lại → export lần nữa có **giống hệt** bản gốc không (sau khi bỏ các trường biến động như ID, thời gian)?
2. Thành phần nào **không** đi qua được, phải làm tay?
3. Ghi lại cùng một cấu hình hai lần có cho kết quả như nhau không (**idempotent**)?
4. Cấu hình có chứa secret / thông tin nhạy cảm ở trường nào?

## Tiêu chí quyết định

| Kết quả | Điều kiện | Hành động |
|---|---|---|
| **Go** | Thành phần cốt lõi (cột, editor, grid, プロセス, ステータス制御, thông báo, script, quyền site) round-trip 100%; phần làm tay < ~20% checklist; idempotent | Chốt ADR-0001 phương án B, sang lát cắt dọc |
| **Đổi hướng** | Cốt lõi đạt nhưng một nhóm quan trọng (vd quyền, cột mở rộng) không round-trip | Thu hẹp phạm vi git, viết runbook cho phần làm tay, cân nhắc site package thay API |
| **No-go** | Cột/editor/プロセス không round-trip ổn định, hoặc không idempotent | Dừng, xem lại chiến lược (ADR-0001 phương án C hoặc mô hình khác) |

## Chuẩn bị

1. Dựng Pleasanter 1.5.x local: xem `env/README.md`. Phải **cùng bản patch** với khách.
2. Tạo API key trên local (user tenant admin, vì API site yêu cầu quyền này).
3. `cp scripts/config.example.json scripts/config.json` và điền thông tin.
4. Python 3.10+, không cần thư viện ngoài.

## Các bước

### Bước 0 — Xác nhận endpoint (30 phút)

Đối chiếu manual 1.5.x xem endpoint lấy/tạo/cập nhật site đúng như trong `config.example.json` (`endpoints`). Nếu khác, sửa trong `config.json`, **không** sửa code.

### Bước 1 — Tạo site mẫu trên local (2–3 giờ)

Tạo bằng tay trên UI local một bộ site **phủ checklist** (`inventory-checklist.md`): ít nhất 1 期限付きテーブル + 1 記録テーブル có liên kết với nhau, có プロセス, ステータス制御, thông báo, リマインダー, server script, client script, style, quyền site/cột, view, công thức, lựa chọn (選択肢).

> Không dùng dữ liệu khách ở bước này. Bước 5 mới dùng cấu hình thật, trong môi trường được phép.

### Bước 2 — Export

```bash
python scripts/export_sites.py --config scripts/config.json --env local --label original
```
Kết quả: `data/local/original/<siteId>.json` (raw) và `.normalized.json`.

### Bước 3 — Round-trip "create" (tạo site mới từ cấu hình đã export)

```bash
python scripts/roundtrip.py --config scripts/config.json --mode create --label original
```
Script tạo site mới dưới `roundtrip_parent_id`, export lại, diff với bản gốc → `data/local/roundtrip-create/report.md`.

### Bước 4 — Round-trip "update" + idempotence

```bash
python scripts/roundtrip.py --config scripts/config.json --mode update --label original --repeat 2
```
Ghi lại cấu hình gốc lên chính site đó 2 lần, export sau mỗi lần, diff. Lần 1 và lần 2 phải không khác nhau.

### Bước 5 — Thử site package (UI)

Export site package của cùng bộ site trên UI → import vào thư mục khác → chạy lại Bước 2 trên site import → so sánh. Ghi nhận site package giữ được gì mà API không giữ (và ngược lại).

Nếu được phép: lặp lại trên **bản sao cấu hình thật của khách** (không dữ liệu) trong môi trường khách cho phép.

### Bước 6 — Đánh giá MCP tích hợp (D1, tùy chọn)

Bật `Parameters/McpServer.json` trên local, kết nối thử, ghi lại danh sách tool và việc nào dùng được cho framework (đọc cấu hình? chỉ record?).

### Bước 7 — Quét secret

```bash
python scripts/scan_secrets.py data/local/original
```
Ghi nhận trường nào chứa URL, token, mail, hostname.

### Bước 8 — Viết báo cáo

Điền `report-template.md`, lưu thành `report-YYYYMMDD.md` (đã làm sạch), cập nhật `docs/review-findings.md` và ADR-0001.

## An toàn

- `scripts/common.py` **chặn mọi lệnh ghi** khi `base_url` không phải localhost. Không nới điều kiện này.
- `data/` bị gitignore. Không commit.
- `report.md` sinh trong `data/` có in **giá trị thật** (trước/sau) để bạn đối chiếu — có thể chứa webhook URL, tên người. Chỉ báo cáo đã làm sạch theo `report-template.md` mới được đưa ra ngoài `data/`.
- Chế độ `create` sẽ khác ở các tham chiếu chéo site (Link, lookup trỏ SiteId cũ) — đánh dấu 🔗 trong báo cáo. Đây là bằng chứng cho yêu cầu phân giải ID xuyên site (A3), không phải lỗi round-trip.
