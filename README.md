# ai-dlc-pleasanter

Framework AI-DLC (AI-Driven Development Lifecycle) của MADLAB dành cho dự án **Pleasanter (プリザンター)**.

Mục tiêu: đưa mô hình "đặt chính bản → AI làm việc qua hook → kiểm tra & người duyệt (G1–G4) → phản hồi lỗi thành quy tắc" vào môi trường low-code, nơi **chính bản là cấu hình** (SiteSettings, script, quyền…) chứ không phải source code.

## Trạng thái

| Hạng mục | Trạng thái |
|---|---|
| Khung repo | ✅ Đã dựng |
| Review thiết kế (A1–C5) | ✅ Ghi tại `docs/review-findings.md` |
| ADR 0001–0005 | 🟡 Template + câu hỏi mở, **chưa chốt** |
| Spike round-trip (B4) | 🟡 Kịch bản + script sẵn sàng, chạy trên Pleasanter dev nội bộ — **chưa chạy** |
| Lát cắt dọc đầu tiên | ⬜ Chờ kết quả spike + ADR |

## Điều kiện môi trường (đã chốt)

- Khách dùng **on-prem**
- Phiên bản **Pleasanter 1.5.x** (ghi chính xác bản patch của dev nội bộ và của khách vào báo cáo spike — hai bên phải trùng)
- Khách **có thể tự sửa cấu hình** trên UI → đồng bộ hai chiều, xử lý drift là bắt buộc

## Phân tách repo

- **Repo này (framework)**: công cụ, quy tắc, ADR, spike chạy trên dữ liệu tổng hợp. **Không** chứa cấu hình hay dữ liệu của khách.
- **Repo dự án (mỗi khách 1 repo)**: cấu hình đã unpack, sổ cái, yêu cầu EARS. Đặt ở nơi khách cho phép.

## Cấu trúc hiện tại

```
ai-dlc-pleasanter/
├─ README.md
├─ CLAUDE.md               # quy tắc cho agent làm việc trong repo
├─ docs/
│  ├─ plan.md              # lộ trình
│  ├─ review-findings.md   # kết quả review kiến trúc → backlog
│  └─ adr/                 # quyết định kiến trúc
└─ spike/round-trip/       # spike B4: cấu hình có khôi phục nguyên vẹn không
   ├─ README.md            # kịch bản, tiêu chí go/no-go
   ├─ env/                 # (tùy chọn) Docker Pleasanter 1.5.x local
   ├─ scripts/             # export / normalize / roundtrip
   ├─ inventory-checklist.md
   ├─ report-template.md
   └─ data/                # (gitignored) dữ liệu export — KHÔNG commit
```

Các thư mục `cli/`, `skills/`, `agents/`, `hooks/`, `test-harness/` **cố ý chưa tạo**. Chúng phụ thuộc kết quả spike và ADR.

## Bắt đầu

1. Đọc `docs/plan.md`.
2. Làm theo `spike/round-trip/README.md`.
