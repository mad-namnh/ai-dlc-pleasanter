# Kết quả review kiến trúc (2026-11-04)

**Kết luận:** Duyệt có điều kiện. Hướng "cấu hình là code + đồng bộ hai chiều + round-trip" đúng. Phải xử lý A1–A3, B1 trước khi đưa lên production của khách.

Mỗi mục là một dòng backlog. Cập nhật cột *Trạng thái* và *Xử lý tại* khi tiến triển.

| ID | Mức | Vấn đề | Đề xuất | Xử lý tại | Trạng thái |
|---|---|---|---|---|---|
| A1 | Critical | Thiết kế chỉ quản lý cấu hình, chưa tính dữ liệu. Ô cột có kiểu cố định; đổi nghĩa ô / ẩn cột trên site có dữ liệu là thay đổi schema. Revert cấu hình được, revert dữ liệu không | Khái niệm **migration**: change đụng dữ liệu kèm script chuyển đổi (bulk upsert) + kế hoạch rollback. CI phân loại *chỉ cấu hình* / *ảnh hưởng dữ liệu* | ADR-0004 | Mở |
| A2 | Critical | Xung đột ô cột: khách thêm cột trên UI (vd NumD), git cũng cấp NumD → đè nhau kèm dữ liệu thật | **Sổ cấp phát ô cột**, chia dải ô theo vùng. Kiểm tra trước deploy chặn khi xung đột | ADR-0002 | Mở |
| A3 | Critical | Không có transaction xuyên site; deploy hỏng giữa chừng → production nửa cũ nửa mới | **Deploy plan**: snapshot → thứ tự theo đồ thị phụ thuộc → áp → smoke test → tự khôi phục. Phân giải ID xử lý tham chiếu chéo site | Bước 4 | Mở |
| B1 | High | Hook không phải ranh giới bảo mật (`curl` vượt được). API key tenant admin quá mạnh | Chặn ở **tầng mạng**. AI không giữ key production; runner trong mạng khách deploy sau G4, key quyền tối thiểu, audit log. Quét secret khi unpack | ADR-0003, ADR-0005 | Mở |
| B2 | High | "Vùng sở hữu" là thỏa thuận tổ chức, không phải kỹ thuật — admin phía khách vẫn sửa được mọi nơi | Ghi vào hợp đồng/SLA. Thực thi bằng phát hiện drift + kiểm tra trước deploy. Báo cáo drift định kỳ | ADR-0002 | Mở |
| B3 | High | Báo cáo diff do AI viết có thể sai → gate an toàn giả | Diff có cấu trúc sinh **tất định** bằng code; AI chỉ diễn đạt lại; luôn kèm bảng diff gốc | Lát cắt #1 | Mở |
| B4 | High | Giả định round-trip chưa kiểm chứng; schema SiteSettings 1.5.x không tài liệu hóa đầy đủ | **Spike có tiêu chí go/no-go** trước mọi việc khác. JSON schema suy ra từ mẫu export thật | `spike/round-trip/` | **Đang làm** |
| C1 | Medium | Core + Adapter là trừu tượng hóa quá sớm | Làm adapter Pleasanter trước; lõi chỉ là quy ước. Tách code chung khi có nền tảng thứ 2 | Đã áp dụng (repo riêng) | Đóng |
| C2 | Medium | Lộ trình chia lớp ngang, không hợp người làm một mình | Lát cắt dọc mỏng | `docs/plan.md` | Đóng |
| C3 | Medium | E2E Playwright trên DOM Pleasanter dễ vỡ | Ưu tiên: kiểm tra tĩnh → test API → ma trận quyền → Playwright chỉ smoke | Bước 4 | Mở |
| C4 | Medium | Dữ liệu on-prem không mang ra ngoài/sang VN được | Seed data tổng hợp. Xác nhận với khách việc lưu cấu hình (không dữ liệu) trong git MADLAB | ADR-0005 | Mở |
| C5 | Medium | Job drift hằng đêm quá thô | Kiểm tra drift trước deploy là chính; job đêm chỉ để báo cáo | Bước 4 | Mở |

## Phát hiện bổ sung (thêm trong quá trình spike)

| ID | Mức | Vấn đề | Đề xuất | Xử lý tại | Trạng thái |
|---|---|---|---|---|---|
| D1 | Info | Pleasanter có **MCP server tích hợp sẵn** (bật qua `Parameters/McpServer.json`, transport HTTP, header `X-Api-Key`, có rate limit và log). Key MCP mang đúng quyền của user phát hành | Đánh giá trong spike: dùng MCP tích hợp cho thao tác record/đọc thay vì tự viết. Dùng user quyền tối thiểu riêng cho AI. Giữ rate limit + logging bật | Spike bước 6 | Mở |
| D2 | Info | Lệnh CodeDefiner thay đổi từ 1.4.6 | Dựng môi trường local theo đúng manual Docker hiện hành cho 1.5.x | `spike/round-trip/env/` | Mở |
