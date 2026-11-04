# Môi trường Pleasanter 1.5.x local (Docker + PostgreSQL)

Dựa trên cách dựng bằng image chính thức `implem/pleasanter`. **Đối chiếu manual Docker hiện hành trước khi chạy** — lệnh CodeDefiner đã thay đổi từ 1.4.6:

- Manual: https://pleasanter.org/ja/manual/getting-started-pleasanter-docker
- Thay đổi CodeDefiner: https://pleasanter.org/ja/manual/codedefiner-changed-steps

## Các bước

1. `cp .env.example .env`, điền mật khẩu và **đúng bản patch 1.5.x của khách** vào `PLEASANTER_VERSION`.
2. Khởi động DB: `docker compose up -d db`
3. Chạy CodeDefiner lần đầu theo manual (khởi tạo DB, ngôn ngữ `ja`, timezone `Asia/Tokyo`). Lệnh mẫu trong `compose.yaml` là service `codedefiner`; **xác nhận tham số với manual** rồi chạy:
   `docker compose run --rm codedefiner`
4. Khởi động: `docker compose up -d pleasanter`
5. Mở http://localhost:50001 — đăng nhập mặc định Administrator / pleasanter, **đổi mật khẩu ngay**.
6. Bật API nếu chưa (`Parameters/Api.json` → `Enabled: true`), tạo API key cho user tenant admin.

## Ghi chú

- Ghi lại chính xác phiên bản đã dùng vào báo cáo spike.
- Muốn reset hoàn toàn: `docker compose down -v` (xóa cả volume DB).
- Không mở cổng ra ngoài máy local.
