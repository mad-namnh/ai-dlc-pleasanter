# Lộ trình ai-dlc-pleasanter

Nguyên tắc: **kiểm chứng giả định lớn nhất trước, rồi làm theo lát cắt dọc mỏng** (xem review C2), không xây theo lớp ngang.

## Bước 1 — Spike round-trip (1–2 tuần) ← ĐANG Ở ĐÂY

Câu hỏi: cấu hình Pleasanter 1.5.x có xuất ra → đưa vào lại → giống hệt bản gốc được không? Phần nào phải làm tay?

- Kịch bản: `spike/round-trip/README.md`
- Đầu ra: báo cáo theo `spike/round-trip/report-template.md` + quyết định **Go / Đổi hướng / No-go**

## Bước 2 — Chốt 5 ADR (≈1 tuần)

| ADR | Chủ đề | Phụ thuộc |
|---|---|---|
| 0001 | Phạm vi cấu hình quản lý trong git | Kết quả spike |
| 0002 | Dải ô cột theo vùng sở hữu | 0001, thỏa thuận với khách |
| 0003 | Cách deploy production | IT phía khách |
| 0004 | Change có ảnh hưởng dữ liệu & gate riêng | 0001 |
| 0005 | Chính sách lưu cấu hình & secret | Hợp đồng/khách |

## Bước 3 — Lát cắt dọc #1

Một site, đi qua toàn bộ chuỗi ở mức tối thiểu:

```
export → unpack → AI sửa → validate (schema + tham chiếu cột)
→ deploy local → 1 test API → diff nghiệp vụ → duyệt → deploy stg (theo deploy plan, có snapshot)
```

Tiêu chí xong: demo được cho khách, chạy lại được bằng một lệnh.

## Bước 4 — Làm dày từng khâu

Theo thứ tự ưu tiên đề xuất (cập nhật sau lát cắt #1):

1. Kiểm tra drift + xung đột ô cột trước deploy (A2, quy tắc trước deploy)
2. Deploy plan: thứ tự phụ thuộc, snapshot, rollback cấu hình (A3)
3. Migration dữ liệu (A1)
4. Ma trận quyền (C3)
5. Skill/agent đầu tiên, chỉ cho những gì case pilot cần

## Bước 5 — Pilot thật & đo lường

Chỉ số:
- Tỉ lệ AI đúng ngay lần đầu
- Số lần người phải sửa, sửa ở đâu
- Thời gian yêu cầu → demo
- Số drift phát sinh / tháng

## Nhật ký quyết định

| Ngày | Quyết định |
|---|---|
| 2026-11-04 | Tách repo framework (`ai-dlc-pleasanter`) và repo dự án khách |
| 2026-11-04 | Điều kiện: on-prem, Pleasanter 1.5.x, khách tự sửa cấu hình được |
