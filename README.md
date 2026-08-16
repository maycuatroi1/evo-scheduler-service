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

## Mô hình bộ giải

Mỗi buổi có đúng hai nhóm biến: tiết bắt đầu và tài nguyên được chọn. Xung đột
chỗ, xung đột lớp và xung đột giáo viên đều diễn đạt bằng khoảng thời gian
(`IntervalVar`) với `AddNoOverlap` / `AddCumulative`, chứ không phải một biến
bool cho mỗi bộ ba buổi x tiết x phòng. Cách cũ sinh hơn 190 nghìn biến trên dữ
liệu một trường thật và bộ giải chạy 600 giây vẫn không kết luận được gì.

Hai điểm cần biết khi sửa phần này:

- **Giải hai pha.** Pha một dựng mô hình không có hàm mục tiêu nên bộ giải dừng
  ngay khi tìm được phương án đầu tiên. Pha hai dựng lại mô hình đầy đủ, lấy
  nghiệm pha một làm gợi ý rồi mới tối ưu. Hết giờ ở pha hai thì phương án pha
  một vẫn được giữ, nên có thời khoá biểu vẫn hơn không có gì.
- **Ràng buộc dư thừa theo nhóm tài nguyên.** `_redundant_pool_capacity` chặn
  trước số buổi diễn ra cùng lúc trên từng nhóm phòng dùng chung. Ràng buộc này
  suy ra được từ những ràng buộc khác nên không đổi tập nghiệm, nhưng thiếu nó
  thì trường hợp thiếu phòng mất hàng chục giây mới kết luận được, có nó thì
  xong trong chưa tới một giây.

Biến `occ` (buổi có chiếm tiết p không) và `on_day` được dựng lười, chỉ khi một
luật hay hàm mục tiêu thật sự hỏi tới.

## Trang thai

Prototype - dang xay dung nen tang. Xem `plans/active/` (o harness repo) de biet thu tu cac buoc.

## License

MIT - xem [LICENSE](./LICENSE).
