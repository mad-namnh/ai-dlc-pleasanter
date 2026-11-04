# CLAUDE.md — quy tắc cho agent trong repo ai-dlc-pleasanter

Giai đoạn hiện tại: **spike + chốt ADR**. Chưa xây skill/agent/hook của framework.

## Bắt buộc

1. **Chỉ ghi vào môi trường dev.** Lệnh ghi (create/update) chỉ được chạy khi đích là localhost, hoặc môi trường khai báo `role: "dev"` **và** `allow_write: true` trong `config.json`. Không bao giờ đặt `role: "dev"` cho môi trường stg/production của khách. Không sửa hay nới `assert_writable` trong `scripts/common.py`. Agent không được tự thêm `--yes` khi người dùng chưa yêu cầu.
2. **Không giữ API key production.** Export từ môi trường khách do người vận hành phía khách hoặc người được ủy quyền chạy. Agent chỉ làm việc trên file đã export.
3. **Không commit dữ liệu khách.** Mọi thứ trong `spike/round-trip/data/` bị gitignore. Không copy cấu hình, tên site, tên người, URL nội bộ của khách vào file khác trong repo. Báo cáo spike phải được làm sạch.
4. **Không commit secret.** `.env`, API key, webhook URL, token nằm ngoài git.
5. **Không đoán về Pleasanter.** Khi không chắc một API/trường cấu hình hoạt động thế nào trên 1.5.x, ghi vào "Câu hỏi mở" của ADR hoặc báo cáo spike, không tự giả định.

## Quy ước

- Tài liệu viết bằng tiếng Việt, giữ thuật ngữ Pleasanter bằng tiếng Nhật (サイト設定, プロセス, 期限付きテーブル…).
- Mỗi quyết định kiến trúc là một ADR trong `docs/adr/`. Không quyết định ngầm trong code.
- Phát hiện mới trong spike → cập nhật `docs/review-findings.md` (thêm mục hoặc đổi mức độ).
