# evo-scheduler-service

Dich vu toi uu hoa thoi khoai bieu (timetable / scheduling) cho he thong EVO LMS.
Service dung [OR-Tools CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver) de bai toan xep lich tro thanh constraint-programming, khong phai heuristic thuan tuy.

## Muc tieu

- Nhap thoi khoai bieu tu Excel, input dang bang (grid) giong cach giao vien lap lich bang tay.
- Bieu dien rang buoc bang CP-SAT: giao vien khong trung gio, phong khong bi chong, mon buoc vao tiet the hien dung yeu cau, nganh/lop khong trung tien do.
- Multi-tenant: moi tenant (don vi truong) co bo rang buoc rieng, biet riets du lieu.
- Tra ve loi giai toi uu (hoac "khong co loi giai" voi bao cao vi phac) qua REST API.

## Kien truc monorepo

```
evo-scheduler-service/
|- backend/      # Django + django-ninja (REST API + CP-SAT worker)
|- frontend/     # Next.js (giao dien import Excel va xem ket qua)
|- docker-compose.yml
|- README.md
|- LICENSE
`- .gitignore
```

### Backend (`backend/`)

- Python 3.11+, Django 5, [django-ninja](https://django-ninja.readthedocs.io/) cho API kieu FastAPI.
- OR-Tools lam lop solver, chay dong bo trong process o giai doan prototype, sau nay tach ra worker (Celery + Redis) khi bai toan to.
- Multi-tenant qua schema `tenant_id` tren cac model (khong dung schema-tenant vi chua can).

### Frontend (`frontend/`)

- Next.js (App Router) + TypeScript + TailwindCSS.
- Man hinh chinh: keo - tha file Excel de import, xem truoc du lieu, bam "Giai" roi xem lich kieu lưới (grid).

## Khung thời khoá biểu

Số tiết khả dụng mỗi tuần là trần cứng của mọi lời giải: một lớp hay một giáo
viên cần nhiều tiết hơn con số này thì không có lịch nào tồn tại. Mặc định là
6 ngày x 5 tiết = 30 tiết; trường học hai buổi phải khai lại.

- Qua giao diện: trang **Ràng buộc**, khối "Khung thời khoá biểu".
- Qua API: `GET/PUT /api/tenant/horizon` với `days_per_week`, `periods_per_day`,
  `morning_count`, `weeks`.
- Qua Excel: sheet **Cấu hình** trong file nhập liệu (không bắt buộc; bỏ trống
  thì giữ nguyên cấu hình đang có).

## Kiểm tra khả thi

`GET /api/schedule/{id}/feasibility` chạy các phép kiểm tra số học trước khi
gọi CP-SAT và chỉ đúng thực thể gây mâu thuẫn: lớp hoặc giáo viên quá tải, buổi
dài hơn một ngày học, thiếu phòng theo loại, buổi bị khoá vào tiết không hợp lệ.
`build_and_solve` cũng chạy đúng bộ kiểm tra này và dừng ngay với trạng thái
`DATA_INFEASIBLE` thay vì đốt hết thời gian giải rồi báo `INFEASIBLE` chung chung.

## Trang thai

Prototype - dang xay dung nen tang. Xem `plans/active/` (o harness repo) de biet thu tu cac buoc.

## License

MIT - xem [LICENSE](./LICENSE).
