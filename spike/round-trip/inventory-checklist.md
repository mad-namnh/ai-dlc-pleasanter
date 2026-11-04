# Checklist thành phần cấu hình — round-trip 1.5.x

Điền sau Bước 3–5. Ký hiệu: ✅ round-trip 100% · 🟡 một phần (ghi rõ) · ❌ không · ➖ chưa thử

**Cốt lõi** = bắt buộc ✅ để đạt Go.

| # | Nhóm | Thành phần | Cốt lõi | API create | API update | Site package | Ghi chú |
|---|---|---|---|---|---|---|---|
| 1 | Bảng | Loại bảng (期限付き / 記録 / フォルダ / Wiki / ダッシュボード) | ✓ | ➖ | ➖ | ➖ | |
| 2 | Cột | Định nghĩa cột (nhãn, kiểu, bắt buộc, mặc định, định dạng) | ✓ | ➖ | ➖ | ➖ | |
| 3 | Cột | 選択肢 (lựa chọn), lựa chọn liên kết site khác | ✓ | ➖ | ➖ | ➖ | Tham chiếu SiteId |
| 4 | Cột | Validation (入力検証), ràng buộc | ✓ | ➖ | ➖ | ➖ | |
| 5 | Cột | Công thức (計算式) | ✓ | ➖ | ➖ | ➖ | |
| 6 | Cột | Cột mở rộng (拡張項目) | | ➖ | ➖ | ➖ | Liên quan ADR-0002 |
| 7 | Màn hình | Editor (EditorColumnHash, tab, セクション) | ✓ | ➖ | ➖ | ➖ | |
| 8 | Màn hình | Grid (GridColumns), filter, sort | ✓ | ➖ | ➖ | ➖ | |
| 9 | Màn hình | View (ビュー) | | ➖ | ➖ | ➖ | |
| 10 | Liên kết | Link giữa các site, lookup (ルックアップ) | ✓ | ➖ | ➖ | ➖ | Tham chiếu chéo SiteId (A3) |
| 11 | Quy trình | プロセス (nút, điều kiện, hành động) | ✓ | ➖ | ➖ | ➖ | |
| 12 | Quy trình | ステータス制御 | ✓ | ➖ | ➖ | ➖ | |
| 13 | Tự động | 通知 (thông báo) | ✓ | ➖ | ➖ | ➖ | Chứa webhook URL? (ADR-0005) |
| 14 | Tự động | リマインダー | | ➖ | ➖ | ➖ | |
| 15 | Code | サーバースクリプト | ✓ | ➖ | ➖ | ➖ | |
| 16 | Code | スクリプト (client) | ✓ | ➖ | ➖ | ➖ | |
| 17 | Code | スタイル | | ➖ | ➖ | ➖ | |
| 18 | Code | HTML (nếu dùng) | | ➖ | ➖ | ➖ | |
| 19 | Code | 拡張SQL | | ➖ | ➖ | ➖ | Có thể là file trên server |
| 20 | Quyền | Quyền site | ✓ | ➖ | ➖ | ➖ | Tham chiếu user/group ID |
| 21 | Quyền | Quyền record, quyền cột | ✓ | ➖ | ➖ | ➖ | |
| 22 | Khác | Xuất/nhập CSV (エクスポート設定) | | ➖ | ➖ | ➖ | |
| 23 | Khác | Tổng hợp, biểu đồ, カレンダー, ガントチャート, カンバン | | ➖ | ➖ | ➖ | |
| 24 | Khác | Tìm kiếm, 一括更新 | | ➖ | ➖ | ➖ | |
| 25 | Ngoài site | User / group / 組織 | | ➖ | ➖ | ➖ | Có thể ngoài phạm vi (ADR-0001) |
| 26 | Ngoài site | Thư mục `Parameters/` trên server | | ➖ | ➖ | ➖ | Quản lý dạng file (IT khách) |
| 27 | Ngoài site | Thiết lập tenant | | ➖ | ➖ | ➖ | |
| 28 | Ngoài site | MCP tích hợp (`McpServer.json`) | | ➖ | ➖ | ➖ | D1 |

## Tổng kết

- Cốt lõi đạt ✅: __ / 15
- Toàn bộ đạt ✅: __ / 28
- Phần phải làm tay: __ % 
