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

## Trang thai

Prototype - dang xay dung nen tang. Xem `plans/active/` (o harness repo) de biet thu tu cac buoc.

## License

MIT - xem [LICENSE](./LICENSE).
