# Phông chữ cho bản in PDF

Ba tệp trong thư mục này được nhúng vào bản xuất PDF (`scheduler/pdf_export.py`).

## Vì sao phải đóng gói kèm

Phông dựng sẵn của reportlab (Helvetica, Vera) **không có dấu tiếng Việt**:
Vera chỉ có 282 glyph và thiếu 14/16 ký tự trong bộ thử `ếộữằọẹâăđơư…`.
Dùng phông đó thì bản in dán bảng tin sẽ mất dấu, vi phạm NFR-5.

Không lấy phông từ hệ thống vì máy chủ chạy Linux, không có Arial; còn
Google Fonts thì không tải được lúc sinh PDF (máy chủ có thể không ra Internet).

## Nguồn và giấy phép

| Tệp | Họ phông | Bản quyền | Giấy phép |
|---|---|---|---|
| `SourceSans3-Regular.ttf` | Source Sans 3 | © 2023 Adobe | SIL OFL 1.1 |
| `SourceSans3-Bold.ttf` | Source Sans 3 | © 2023 Adobe | SIL OFL 1.1 |
| `BarlowCondensed-SemiBold.ttf` | Barlow Condensed | © 2017 The Barlow Project Authors | SIL OFL 1.1 |

Toàn văn giấy phép: <https://scripts.sil.org/OFL>

SIL OFL 1.1 cho phép đóng gói lại và nhúng vào tài liệu, kể cả dùng cho
mục đích thương mại. Điều kiện: giữ nguyên thông báo bản quyền và không
bán riêng phông.

Hai họ phông này trùng với phông giao diện web (`frontend/app/layout.tsx`)
nên bản in và màn hình nhìn thống nhất.
