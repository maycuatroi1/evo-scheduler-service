"""Kiểm chứng việc sinh buổi học từ số giờ chương trình."""

from django.test import TestCase

from scheduler import session_builder
from scheduler.models import (
    HomeroomClass,
    Module,
    Schedule,
    Session,
    StudentGroup,
    Tenant,
)


class SessionBuilderTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(code="CUWC", name="CUWC")
        self.sched = Schedule.objects.create(tenant=self.tenant, name="TKB")

    def _group(self, code="G1", size=16, hazardous=False):
        return StudentGroup.objects.create(
            tenant=self.tenant,
            code=code,
            name=code,
            enrollment_type="dual_degree",
            size=size,
            hazardous=hazardous,
        )

    def _module(self, code="MD1", lt=0, th=0, group=None):
        return Module.objects.create(
            tenant=self.tenant,
            code=code,
            name=code,
            theory_hours=lt,
            practice_hours=th,
            student_group=group,
        )

    # ---------- chia buổi ----------

    def test_gio_ly_thuyet_chia_thanh_buoi_2_tiet(self):
        g = self._group()
        self._module("MD1", lt=6, group=g)
        plans = session_builder.plan(self.tenant)
        lt = [p for p in plans if p.session_type == "theory"]
        self.assertEqual(sum(p.count for p in lt), 3)
        self.assertTrue(all(p.slots_each == 2 for p in lt))

    def test_gio_thuc_hanh_gop_buoi_dai_hon(self):
        """Trên bản in, mô-đun thực hành chiếm trọn buổi 3–5 tiết."""
        g = self._group()
        self._module("MD2", th=9, group=g)
        plans = session_builder.plan(self.tenant)
        th = [p for p in plans if p.session_type == "practice"]
        self.assertEqual(sum(p.count for p in th), 3)
        self.assertTrue(all(p.slots_each == 3 for p in th))

    def test_phan_du_thanh_buoi_ngan(self):
        g = self._group()
        self._module("MD3", lt=5, group=g)  # 2 + 2 + 1
        plans = session_builder.plan(self.tenant)
        lens = sorted(
            [p.slots_each for p in plans for _ in range(p.count)], reverse=True
        )
        self.assertEqual(lens, [2, 2, 1])

    def test_buoi_khong_dai_qua_mot_buoi_hoc(self):
        """Buổi không được vắt qua ngày."""
        g = self._group()
        self._module("MD4", th=12, group=g)
        plans = session_builder.plan(self.tenant, max_slots_per_day=2)
        self.assertTrue(all(p.slots_each <= 2 for p in plans))

    # ---------- trần sĩ số nhân số buổi ----------

    def test_nhom_38_hs_chia_ba_ca_thuc_hanh(self):
        """Dữ liệu thật: nhóm Điện CN&DD có 38 HS, trần thực hành 18."""
        g = self._group("G3", size=38)
        self._module("MD5", th=6, group=g)
        plans = session_builder.plan(self.tenant)
        th = [p for p in plans if p.session_type == "practice"]
        self.assertEqual(th[0].batches, 3)
        # 2 buổi × 3 ca = 6 buổi
        self.assertEqual(sum(p.count for p in th), 6)
        self.assertIn("chia 3 ca", th[0].note)

    def test_nghe_doc_hai_ap_tran_10(self):
        g = self._group("G9", size=25, hazardous=True)
        self._module("MD6", th=3, group=g)
        plans = session_builder.plan(self.tenant)
        th = [p for p in plans if p.session_type == "practice"]
        self.assertEqual(th[0].batches, 3)

    def test_ly_thuyet_ap_tran_35_khong_phai_18(self):
        g = self._group("G5", size=30)
        self._module("MD7", lt=2, group=g)
        plans = session_builder.plan(self.tenant)
        lt = [p for p in plans if p.session_type == "theory"]
        self.assertEqual(lt[0].batches, 1, "Lý thuyết trần 35 nên 30 HS học nguyên ca")

    def test_nhom_nho_khong_chia_ca(self):
        g = self._group("G1", size=16)
        self._module("MD8", th=3, group=g)
        plans = session_builder.plan(self.tenant)
        self.assertEqual(plans[0].batches, 1)

    # ---------- ghi vào cơ sở dữ liệu ----------

    def test_sinh_buoi_hoc_that(self):
        g = self._group()
        self._module("MD9", lt=4, th=6, group=g)
        r = session_builder.apply(self.tenant, self.sched)
        self.assertEqual(r["created"], 4)  # 2 buổi LT + 2 buổi TH
        self.assertEqual(Session.objects.filter(schedule=self.sched).count(), 4)
        self.assertEqual(r["total_periods"], 10)

    def test_chay_lai_khong_nhan_doi(self):
        g = self._group()
        self._module("MDA", lt=4, group=g)
        session_builder.apply(self.tenant, self.sched)
        session_builder.apply(self.tenant, self.sched)
        self.assertEqual(Session.objects.filter(schedule=self.sched).count(), 2)

    def test_buoi_da_khoa_duoc_giu_nguyen(self):
        """Chạy lại không được làm mất công tinh chỉnh."""
        g = self._group()
        m = self._module("MDB", lt=4, group=g)
        Session.objects.create(
            tenant=self.tenant,
            schedule=self.sched,
            module=m,
            student_group=g,
            session_type="theory",
            tier="vocational",
            is_locked=True,
            assigned_timeslot={"day": 0, "period": 0, "week": 0},
        )
        r = session_builder.apply(self.tenant, self.sched)
        self.assertEqual(r["removed"], 0, "Buổi đã khoá không bị xoá")
        locked = Session.objects.filter(schedule=self.sched, is_locked=True)
        self.assertEqual(locked.count(), 1)

    def test_buoi_da_ghim_duoc_giu_nguyen(self):
        g = self._group()
        m = self._module("MDC", lt=2, group=g)
        Session.objects.create(
            tenant=self.tenant,
            schedule=self.sched,
            module=m,
            student_group=g,
            session_type="theory",
            tier="culture",
            is_pinned=True,
        )
        session_builder.apply(self.tenant, self.sched)
        self.assertEqual(
            Session.objects.filter(schedule=self.sched, is_pinned=True).count(), 1
        )

    def test_mon_van_hoa_gan_dung_khoi(self):
        g = self._group()
        self._module("VH01", lt=4, group=g)
        plans = session_builder.plan(self.tenant)
        self.assertEqual(plans[0].tier, "culture")

    def test_mo_dun_khong_co_gio_thi_khong_sinh_buoi(self):
        g = self._group()
        self._module("MDD", lt=0, th=0, group=g)
        plans = session_builder.plan(self.tenant)
        self.assertEqual(len(plans), 0)


class BuildApiTests(TestCase):
    """Endpoint xem trước và sinh buổi học."""

    def setUp(self):
        from django.test import Client

        from scheduler.accounts import hash_password, mint_token
        from scheduler.models import User

        self.c = Client()
        self.tenant = Tenant.objects.create(code="T", name="T")
        self.pdt = User.objects.create(
            tenant=self.tenant,
            email="pdt@x.vn",
            name="PDT",
            password_hash=hash_password("x"),
            role="registrar",
        )
        self.gv = User.objects.create(
            tenant=self.tenant,
            email="gv@x.vn",
            name="GV",
            password_hash=hash_password("x"),
            role="teacher",
        )
        self.h = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(self.pdt)}
        self.hgv = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(self.gv)}
        self.sched = Schedule.objects.create(tenant=self.tenant, name="TKB")
        g = StudentGroup.objects.create(
            tenant=self.tenant,
            code="G3",
            name="Dien CN",
            enrollment_type="dual_degree",
            size=38,
        )
        Module.objects.create(
            tenant=self.tenant,
            code="MD1",
            name="May dien",
            theory_hours=4,
            practice_hours=6,
            student_group=g,
        )

    def test_xem_truoc_khong_ghi_du_lieu(self):
        r = self.c.get(
            f"/api/v2/schedule/{self.sched.id}/build-preview", **self.h
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.json()["total_sessions"], 0)
        self.assertEqual(Session.objects.count(), 0, "Xem trước không được ghi")

    def test_sinh_buoi_hoc_qua_api(self):
        import json

        r = self.c.post(
            f"/api/v2/schedule/{self.sched.id}/build-sessions",
            data=json.dumps({}),
            content_type="application/json",
            **self.h,
        )
        self.assertEqual(r.status_code, 200)
        # LT 4 giờ = 2 buổi (nhóm 38 HS, trần LT 35 nên chia 2 ca) = 4
        # TH 6 giờ = 2 buổi × 3 ca = 6
        self.assertEqual(r.json()["created"], 10)

    def test_giao_vien_khong_duoc_sinh_buoi(self):
        import json

        r = self.c.post(
            f"/api/v2/schedule/{self.sched.id}/build-sessions",
            data=json.dumps({}),
            content_type="application/json",
            **self.hgv,
        )
        self.assertEqual(r.status_code, 403)


class ImportModeTests(TestCase):
    """Chế độ nhập: merge giữ dữ liệu, replace xoá sạch."""

    def setUp(self):
        from scheduler.models import Resource, Teacher

        self.tenant = Tenant.objects.create(code="T", name="T")
        self.teacher = Teacher.objects.create(
            tenant=self.tenant, code="GV01", name="Ten cu", quota_standard_hours=500
        )
        self.group = StudentGroup.objects.create(
            tenant=self.tenant, code="G1", name="Nhom cu",
            enrollment_type="dual_degree", size=20,
        )
        self.room = Resource.objects.create(
            tenant=self.tenant, code="P1", name="Phong cu", type="theory_room"
        )
        self.module = Module.objects.create(
            tenant=self.tenant, code="M1", name="Mon cu", theory_hours=10
        )
        self.sched = Schedule.objects.create(tenant=self.tenant, name="TKB")

    def _parsed(self, teacher_name="Ten moi"):
        return {
            "Teachers": [{"code": "GV01", "name": teacher_name, "blocks": "Nghe"}],
            "StudentGroups": [],
            "Resources": [],
            "Modules": [],
            "TeacherModule": [],
            "FixedSessions": [],
            "Config": [],
        }

    def test_merge_cap_nhat_thay_vi_tao_trung(self):
        from config.api import _persist
        from scheduler.models import Teacher

        r = _persist(self._parsed(), self.tenant, mode="merge")
        self.assertEqual(Teacher.objects.filter(tenant=self.tenant).count(), 1)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.name, "Ten moi")
        self.assertEqual(r.get("updated", 0), 1)
        self.assertEqual(r["teachers"], 0, "Cập nhật không tính là tạo mới")

    def test_merge_giu_du_lieu_khong_co_trong_file(self):
        """Nhập file chỉ có giáo viên thì lớp, phòng, môn phải còn nguyên."""
        from config.api import _persist
        from scheduler.models import Resource

        _persist(self._parsed(), self.tenant, mode="merge")
        self.assertEqual(StudentGroup.objects.filter(tenant=self.tenant).count(), 1)
        self.assertEqual(Resource.objects.filter(tenant=self.tenant).count(), 1)
        self.assertEqual(Module.objects.filter(tenant=self.tenant).count(), 1)

    def test_replace_xoa_sach_du_lieu_cu(self):
        from config.api import _persist
        from scheduler.models import Resource

        r = _persist(self._parsed(), self.tenant, mode="replace")
        self.assertTrue(r.get("deleted_all"))
        self.assertEqual(StudentGroup.objects.filter(tenant=self.tenant).count(), 0)
        self.assertEqual(Resource.objects.filter(tenant=self.tenant).count(), 0)

    def test_merge_giu_buoi_da_khoa(self):
        """Nhập lại không được làm mất công tinh chỉnh."""
        from config.api import _persist

        Session.objects.create(
            tenant=self.tenant, schedule=self.sched, module=self.module,
            student_group=self.group, session_type="theory", tier="vocational",
            is_locked=True,
        )
        parsed = self._parsed()
        parsed["FixedSessions"] = [
            {"module_code": "M1", "student_group_code": "G1",
             "session_type": "Ly thuyet", "duration_slots": 2, "tier": "Nghe"}
        ]
        parsed["Modules"] = [{"code": "M1", "name": "Mon cu", "theory_hours": 10}]
        parsed["StudentGroups"] = [
            {"code": "G1", "name": "Nhom cu", "enrollment_type": "Song bang", "size": 20}
        ]
        _persist(parsed, self.tenant, mode="merge")
        self.assertEqual(
            Session.objects.filter(tenant=self.tenant, is_locked=True).count(),
            1,
            "Buổi đã khoá phải được giữ",
        )

    def test_merge_khong_nhan_doi_buoi_hoc(self):
        from config.api import _persist

        parsed = self._parsed()
        parsed["Modules"] = [{"code": "M1", "name": "M", "theory_hours": 10}]
        parsed["StudentGroups"] = [
            {"code": "G1", "name": "G", "enrollment_type": "Song bang", "size": 20}
        ]
        parsed["FixedSessions"] = [
            {"module_code": "M1", "student_group_code": "G1",
             "session_type": "Ly thuyet", "duration_slots": 2, "tier": "Nghe"}
        ]
        _persist(parsed, self.tenant, mode="merge")
        n1 = Session.objects.filter(tenant=self.tenant).count()
        _persist(parsed, self.tenant, mode="merge")
        n2 = Session.objects.filter(tenant=self.tenant).count()
        self.assertEqual(n1, n2, "Nhập lại cùng file không được nhân đôi buổi học")

    def test_che_do_khong_hop_le_bi_chan(self):
        import json

        from django.test import Client

        from scheduler.accounts import hash_password, mint_token
        from scheduler.models import User

        u = User.objects.create(
            tenant=self.tenant, email="a@b.c", name="A",
            password_hash=hash_password("x"), role="registrar",
        )
        c = Client()
        r = c.post(
            "/api/import/commit?mode=sai",
            data={"file": __import__("io").BytesIO(b"x")},
            HTTP_AUTHORIZATION="Bearer " + mint_token(u),
        )
        self.assertIn(r.status_code, (400, 422))
