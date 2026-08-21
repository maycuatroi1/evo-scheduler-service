"""Kiểm chứng API nghiệp vụ trường nghề."""

import json

from django.test import Client, TestCase

from scheduler.accounts import hash_password, mint_token
from scheduler.models import (
    ConstraintRule,
    HomeroomClass,
    Module,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    Tenant,
    User,
)

V2 = "/api/v2"


class ApiBase(TestCase):
    def setUp(self):
        self.c = Client()
        self.tenant = Tenant.objects.create(code="CUWC", name="CUWC")
        self.pdt = User.objects.create(
            tenant=self.tenant,
            email="pdt@cuwc.edu.vn",
            name="Phong Dao tao",
            password_hash=hash_password("x"),
            role="registrar",
        )
        self.gv = User.objects.create(
            tenant=self.tenant,
            email="gv@cuwc.edu.vn",
            name="Giao vien",
            password_hash=hash_password("x"),
            role="teacher",
        )
        self.h_pdt = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(self.pdt)}
        self.h_gv = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(self.gv)}

    def post(self, url, data, headers):
        return self.c.post(
            url, data=json.dumps(data), content_type="application/json", **headers
        )

    def put(self, url, data, headers):
        return self.c.put(
            url, data=json.dumps(data), content_type="application/json", **headers
        )


class PermissionTests(ApiBase):
    """Giáo viên chỉ được xem; Phòng Đào tạo mới được sửa."""

    def test_giao_vien_khong_duoc_tao_du_lieu(self):
        r = self.post(
            V2 + "/homerooms", {"code": "11A3", "size": 63}, self.h_gv
        )
        self.assertEqual(r.status_code, 403)

    def test_phong_dao_tao_duoc_tao_du_lieu(self):
        r = self.post(
            V2 + "/homerooms", {"code": "11A3", "size": 63}, self.h_pdt
        )
        self.assertEqual(r.status_code, 201)

    def test_giao_vien_van_xem_duoc(self):
        r = self.c.get(V2 + "/homerooms", **self.h_gv)
        self.assertEqual(r.status_code, 200)

    def test_khong_co_token_thi_chan(self):
        r = self.c.get(V2 + "/homerooms")
        self.assertEqual(r.status_code, 401)


class HomeroomGroupTests(ApiBase):
    """Quan hệ lớp văn hoá và nhóm nghề, dữ liệu thật của trường."""

    def test_lop_11A3_tach_ba_nhom(self):
        r = self.post(
            V2 + "/homerooms",
            {"code": "11A3", "grade": 11, "size": 63, "culture_shift": "afternoon"},
            self.h_pdt,
        )
        hid = r.json()["id"]
        for code, name, si in [
            ("G1", "CNKT Dieu khien tu dong", 16),
            ("G4", "Thiet ke noi that", 17),
            ("G5", "Cong nghe o to 1", 30),
        ]:
            self.post(
                V2 + "/groups",
                {"code": code, "name": name, "size": si, "homeroom_ids": [hid]},
                self.h_pdt,
            )
        r = self.c.get(V2 + "/homerooms/%d/split" % hid, **self.h_pdt)
        data = r.json()
        self.assertTrue(data["is_split"])
        self.assertEqual(data["group_count"], 3)
        self.assertEqual(data["total_in_groups"], 63)

    def test_nhieu_lop_gop_mot_nhom(self):
        a = self.post(V2 + "/homerooms", {"code": "12A1", "size": 30}, self.h_pdt).json()
        b = self.post(V2 + "/homerooms", {"code": "12A4", "size": 14}, self.h_pdt).json()
        r = self.post(
            V2 + "/groups",
            {
                "code": "M3",
                "name": "KT lap dat dien",
                "size": 44,
                "homeroom_ids": [a["id"], b["id"]],
            },
            self.h_pdt,
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(sorted(r.json()["homeroom_codes"]), ["12A1", "12A4"])

    def test_ca_nghe_suy_tu_ca_van_hoa(self):
        r = self.post(
            V2 + "/homerooms",
            {"code": "11A1", "grade": 11, "culture_shift": "afternoon"},
            self.h_pdt,
        )
        self.assertEqual(r.json()["vocational_shift"], "morning")

    def test_so_ca_thuc_hanh_theo_tran_si_so(self):
        """Nhóm 38 HS phải chia 3 ca vì trần thực hành là 18."""
        r = self.post(
            V2 + "/groups", {"code": "G3", "name": "Dien CN", "size": 38}, self.h_pdt
        )
        self.assertEqual(r.json()["practice_batches"], 3)

    def test_nghe_doc_hai_chia_theo_tran_10(self):
        r = self.post(
            V2 + "/groups",
            {"code": "G9", "name": "Han", "size": 25, "hazardous": True},
            self.h_pdt,
        )
        self.assertEqual(r.json()["practice_batches"], 3)

    def test_ma_trung_bi_chan(self):
        self.post(V2 + "/homerooms", {"code": "11A3"}, self.h_pdt)
        r = self.post(V2 + "/homerooms", {"code": "11A3"}, self.h_pdt)
        self.assertEqual(r.status_code, 400)


class RulePriorityTests(ApiBase):
    def test_dat_do_uu_tien_lam_doi_trong_so_hieu_dung(self):
        r = self.post(
            V2 + "/rules",
            {"type": "preference", "weight": 3, "priority": "low"},
            self.h_pdt,
        )
        rid = r.json()["id"]
        self.assertEqual(r.json()["effective_weight"], 3)
        r2 = self.put(
            V2 + "/rules/%d/priority" % rid, {"priority": "high"}, self.h_pdt
        )
        self.assertEqual(r2.json()["effective_weight"], 15)

    def test_loai_rang_buoc_khong_hop_le_bi_chan(self):
        r = self.post(V2 + "/rules", {"type": "khong_ton_tai"}, self.h_pdt)
        self.assertEqual(r.status_code, 400)

    def test_luu_duoc_rang_buoc_dac_thu_truong_nghe(self):
        for t in ("group_same_class", "shift_by_grade", "capacity_by_type"):
            r = self.post(V2 + "/rules", {"type": t}, self.h_pdt)
            self.assertEqual(r.status_code, 201, t)


class WorkloadTests(ApiBase):
    def test_quy_doi_gio_chuan(self):
        """45 phút LT = 1 giờ chuẩn; tiết TH 45 phút quy đổi 0,75."""
        t = Teacher.objects.create(
            tenant=self.tenant, code="GV011", name="Khanh", quota_standard_hours=550
        )
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G1", name="G1", enrollment_type="dual_degree"
        )
        m = Module.objects.create(tenant=self.tenant, code="MD1", name="M")
        for stype, dur in [("theory", 4), ("practice", 4)]:
            s = Session.objects.create(
                tenant=self.tenant,
                module=m,
                student_group=g,
                session_type=stype,
                tier="vocational",
                duration_slots=dur,
            )
            s.assigned_teachers.add(t)
        r = self.c.get(V2 + "/reports/teacher-workload", **self.h_pdt)
        row = r.json()["teachers"][0]
        self.assertEqual(row["theory_periods"], 4)
        self.assertEqual(row["practice_periods"], 4)
        self.assertEqual(row["standard_hours"], 7.0)  # 4*1 + 4*0.75

    def test_buoi_thuc_tap_khong_tinh_dinh_muc(self):
        t = Teacher.objects.create(tenant=self.tenant, code="GV02", name="X")
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G2", name="G2", enrollment_type="college"
        )
        m = Module.objects.create(tenant=self.tenant, code="MD2", name="M")
        s = Session.objects.create(
            tenant=self.tenant,
            module=m,
            student_group=g,
            session_type="internship",
            tier="vocational",
            duration_slots=50,
        )
        s.assigned_teachers.add(t)
        r = self.c.get(V2 + "/reports/teacher-workload", **self.h_pdt)
        row = [x for x in r.json()["teachers"] if x["code"] == "GV02"][0]
        self.assertEqual(row["standard_hours"], 0)


class PublishTests(ApiBase):
    def test_chi_xuat_ban_duoc_lich_da_giai(self):
        sc = Schedule.objects.create(tenant=self.tenant, name="Nhap", status="draft")
        r = self.post(V2 + "/schedule/%d/publish" % sc.id, {}, self.h_pdt)
        self.assertEqual(r.status_code, 400)

    def test_xuat_ban_ghi_nhan_nguoi_va_thoi_diem(self):
        sc = Schedule.objects.create(tenant=self.tenant, name="TKB", status="solved")
        r = self.post(V2 + "/schedule/%d/publish" % sc.id, {}, self.h_pdt)
        self.assertEqual(r.status_code, 200)
        sc.refresh_from_db()
        self.assertEqual(sc.status, "published")
        self.assertIsNotNone(sc.published_at)
        self.assertEqual(sc.published_by_id, self.pdt.id)

    def test_giao_vien_khong_duoc_xuat_ban(self):
        sc = Schedule.objects.create(tenant=self.tenant, name="TKB", status="solved")
        r = self.post(V2 + "/schedule/%d/publish" % sc.id, {}, self.h_gv)
        self.assertEqual(r.status_code, 403)


class InheritTests(ApiBase):
    def _sess(self, sched, mod, grp, teacher, slot=None):
        s = Session.objects.create(
            tenant=self.tenant,
            schedule=sched,
            module=mod,
            student_group=grp,
            session_type="theory",
            tier="vocational",
            assigned_timeslot=slot,
        )
        s.assigned_teachers.add(teacher)
        return s

    def test_do_giao_vien_doi_phan_cong(self):
        base = Schedule.objects.create(tenant=self.tenant, name="HK1", status="solved")
        new = Schedule.objects.create(tenant=self.tenant, name="HK2", status="draft")
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="dual_degree"
        )
        m1 = Module.objects.create(tenant=self.tenant, code="M1", name="M1")
        m2 = Module.objects.create(tenant=self.tenant, code="M2", name="M2")
        giu = Teacher.objects.create(tenant=self.tenant, code="GV_GIU", name="Giu")
        doi = Teacher.objects.create(tenant=self.tenant, code="GV_DOI", name="Doi")

        self._sess(base, m1, g, giu, {"day": 0, "period": 1, "week": 0})
        self._sess(base, m2, g, doi, {"day": 1, "period": 1, "week": 0})
        # Sang kỳ mới, GV_DOI nhận thêm mô-đun M1
        self._sess(new, m1, g, giu)
        s = self._sess(new, m2, g, doi)
        s.assigned_teachers.add(giu)

        r = self.c.get(
            V2 + "/schedule/%d/inherit-diff?base_id=%d" % (new.id, base.id),
            **self.h_pdt
        )
        data = r.json()
        codes = {x["teacher_code"] for x in data["changed"]}
        self.assertIn("GV_GIU", codes, "GV nhận thêm mô-đun phải bị đánh dấu đổi")
        self.assertLess(data["keep_pct"], 100.0)

    def test_ke_thua_sao_chep_vi_tri_tiet(self):
        base = Schedule.objects.create(tenant=self.tenant, name="HK1", status="solved")
        new = Schedule.objects.create(tenant=self.tenant, name="HK2", status="draft")
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="dual_degree"
        )
        m = Module.objects.create(tenant=self.tenant, code="M1", name="M1")
        t = Teacher.objects.create(tenant=self.tenant, code="GV1", name="A")
        self._sess(base, m, g, t, {"day": 2, "period": 3, "week": 0})
        target = self._sess(new, m, g, t)

        r = self.post(
            V2 + "/schedule/%d/inherit" % new.id,
            {"base_id": base.id, "keep_level": "max"},
            self.h_pdt,
        )
        self.assertEqual(r.json()["copied"], 1)
        target.refresh_from_db()
        self.assertEqual(target.assigned_timeslot["day"], 2)
        self.assertTrue(target.is_locked)
        new.refresh_from_db()
        self.assertEqual(new.inherited_from_id, base.id)


class BellTimeTests(ApiBase):
    def test_sinh_moc_gio_tu_tham_so(self):
        r = self.put(
            V2 + "/tenant/bell-times",
            {
                "morning_start": "07:00",
                "period_minutes": 45,
                "break_minutes": 5,
                "long_break_after": 2,
                "long_break_minutes": 15,
            },
            self.h_pdt,
        )
        rows = r.json()["periods"]["morning"]
        self.assertEqual(rows[0]["start"], "07:00")
        self.assertEqual(rows[0]["end"], "07:45")
        self.assertEqual(rows[1]["start"], "07:50")
        # Sau tiết 2 nghỉ dài 15 phút
        self.assertEqual(rows[2]["start"], "08:55")

    def test_chao_co_725_nam_trong_tiet_1(self):
        r = self.c.get(V2 + "/tenant/bell-times", **self.h_pdt)
        t1 = r.json()["periods"]["morning"][0]
        self.assertLessEqual(t1["start"], "07:25")
        self.assertGreaterEqual(t1["end"], "07:25")


class PinTests(ApiBase):
    def test_ghim_va_bo_ghim(self):
        sc = Schedule.objects.create(tenant=self.tenant, name="TKB")
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="dual_degree"
        )
        m = Module.objects.create(tenant=self.tenant, code="CC", name="Chao co")
        s = Session.objects.create(
            tenant=self.tenant, schedule=sc, module=m, student_group=g,
            session_type="theory", tier="culture",
        )
        r = self.post(
            V2 + "/schedule/%d/pins" % sc.id,
            {"session_id": s.id, "day": 0, "period": 0},
            self.h_pdt,
        )
        self.assertEqual(r.status_code, 200)
        s.refresh_from_db()
        self.assertTrue(s.is_pinned)
        self.assertTrue(s.is_locked)

        self.c.delete(
            V2 + "/schedule/%d/pins/%d" % (sc.id, s.id), **self.h_pdt
        )
        s.refresh_from_db()
        self.assertFalse(s.is_pinned)


class ResourceTests(ApiBase):
    """Phòng, xưởng và báo cáo suất sử dụng."""

    def test_tao_va_liet_ke_phong(self):
        r = self.post(
            V2 + "/resources",
            {"code": "A11-204", "name": "Xuong dien", "type": "workshop",
             "capacity": 18, "quantity": 1, "available_quantity": 1},
            self.h_pdt,
        )
        self.assertEqual(r.status_code, 201)
        rs = self.c.get(V2 + "/resources", **self.h_pdt).json()
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs[0]["code"], "A11-204")

    def test_loc_theo_loai_phong(self):
        self.post(
            V2 + "/resources",
            {"code": "A6-501", "name": "Phong VH", "type": "theory_room"},
            self.h_pdt,
        )
        self.post(
            V2 + "/resources",
            {"code": "A10-XTH", "name": "Xuong o to", "type": "workshop"},
            self.h_pdt,
        )
        rs = self.c.get(V2 + "/resources?type=workshop", **self.h_pdt).json()
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs[0]["code"], "A10-XTH")

    def test_loai_phong_khong_hop_le_bi_chan(self):
        r = self.post(
            V2 + "/resources", {"code": "X", "name": "X", "type": "sai"}, self.h_pdt
        )
        self.assertEqual(r.status_code, 400)

    def test_giao_vien_khong_duoc_tao_phong(self):
        r = self.post(
            V2 + "/resources", {"code": "Y", "name": "Y"}, self.h_gv
        )
        self.assertEqual(r.status_code, 403)

    def test_bao_cao_suat_su_dung_phong(self):
        from scheduler.models import Resource

        room = Resource.objects.create(
            tenant=self.tenant, code="A11-204", name="Xuong",
            type="workshop", capacity=18, quantity=1, available_quantity=1,
        )
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="dual_degree"
        )
        m = Module.objects.create(tenant=self.tenant, code="M", name="M")
        Session.objects.create(
            tenant=self.tenant, module=m, student_group=g,
            session_type="practice", tier="vocational",
            duration_slots=3, assigned_resource=room,
        )
        r = self.c.get(V2 + "/reports/room-usage", **self.h_pdt).json()
        row = [x for x in r["rooms"] if x["code"] == "A11-204"][0]
        self.assertEqual(row["periods_used"], 3)
        self.assertGreater(row["usage_pct"], 0)

    def test_buoi_thuc_tap_khong_tinh_suat_dung_phong(self):
        from scheduler.models import Resource

        room = Resource.objects.create(
            tenant=self.tenant, code="A11-103", name="X",
            type="workshop", quantity=1, available_quantity=1,
        )
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G2", name="G2", enrollment_type="college"
        )
        m = Module.objects.create(tenant=self.tenant, code="M2", name="M2")
        Session.objects.create(
            tenant=self.tenant, module=m, student_group=g,
            session_type="internship", tier="vocational",
            duration_slots=50, assigned_resource=room,
        )
        r = self.c.get(V2 + "/reports/room-usage", **self.h_pdt).json()
        row = [x for x in r["rooms"] if x["code"] == "A11-103"][0]
        self.assertEqual(row["periods_used"], 0)


class StopSolveTests(ApiBase):
    """Người dùng bấm Dừng: bộ giải phải giữ lại phương án đã tìm được."""

    def _job(self, status="solving"):
        from scheduler.models import SolveJob

        sch = Schedule.objects.create(
            tenant=self.tenant, name="HK1", status="solving"
        )
        return SolveJob.objects.create(
            tenant=self.tenant, schedule=sch, status=status
        )

    def test_dat_co_dung_cho_phien_dang_chay(self):
        from scheduler.models import SolveJob

        job = self._job()
        r = self.post(V2 + "/solve/%s/stop" % job.id, {}, self.h_pdt)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["stopped"])
        self.assertTrue(
            SolveJob.objects.get(id=job.id).stop_requested
        )

    def test_phien_da_ket_thuc_thi_khong_dung_nua(self):
        from scheduler.models import SolveJob

        job = self._job(status=SolveJob.Status.SOLVED)
        r = self.post(V2 + "/solve/%s/stop" % job.id, {}, self.h_pdt)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["stopped"])
        self.assertFalse(SolveJob.objects.get(id=job.id).stop_requested)

    def test_giao_vien_khong_duoc_dung_bo_giai(self):
        job = self._job()
        r = self.post(V2 + "/solve/%s/stop" % job.id, {}, self.h_gv)
        self.assertEqual(r.status_code, 403)

    def test_phien_cua_truong_khac_tra_ve_404(self):
        from scheduler.models import SolveJob

        other = Tenant.objects.create(code="X", name="X")
        sch = Schedule.objects.create(tenant=other, name="HK1")
        job = SolveJob.objects.create(
            tenant=other, schedule=sch, status="solving"
        )
        r = self.post(V2 + "/solve/%s/stop" % job.id, {}, self.h_pdt)
        self.assertEqual(r.status_code, 404)

    def test_ma_phien_sai_dinh_dang_tra_ve_404(self):
        r = self.post(V2 + "/solve/khong-phai-uuid/stop", {}, self.h_pdt)
        self.assertEqual(r.status_code, 404)

    def test_tac_vu_ghi_trang_thai_da_dung(self):
        """Bấm Dừng trước khi tác vụ chạy xong -> trạng thái là stopped."""
        from scheduler.models import SolveJob
        from scheduler.tasks import solve_schedule

        job = self._job()
        job.stop_requested = True
        job.save(update_fields=["stop_requested"])

        out = solve_schedule(job.schedule_id, {"solve_job_id": str(job.id)})
        self.assertEqual(out["status"], "stopped")
        self.assertEqual(
            SolveJob.objects.get(id=job.id).status, SolveJob.Status.STOPPED
        )


class ModuleCrudTests(ApiBase):
    """CRUD mô-đun cho màn hình /mo-dun."""

    def _mk(self, code="MD01", **kw):
        kw.setdefault("name", "Kỹ thuật điện")
        kw.setdefault("theory_hours", 30)
        kw.setdefault("practice_hours", 60)
        return self.post(V2 + "/modules", {"code": code, **kw}, self.h_pdt)

    def test_tao_va_liet_ke_mo_dun(self):
        r = self._mk()
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["total_hours"], 90)
        rows = self.c.get(V2 + "/modules", **self.h_pdt).json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["code"], "MD01")

    def test_ma_trung_bi_tu_choi(self):
        self._mk()
        r = self._mk()
        self.assertEqual(r.status_code, 400)

    def test_sua_mo_dun(self):
        mid = self._mk().json()["id"]
        r = self.put(
            V2 + "/modules/%d" % mid,
            {"code": "MD01", "name": "Đã đổi", "theory_hours": 10,
             "practice_hours": 20},
            self.h_pdt,
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["name"], "Đã đổi")
        self.assertEqual(r.json()["total_hours"], 30)

    def test_xoa_mo_dun_khong_con_buoi(self):
        mid = self._mk().json()["id"]
        r = self.c.delete(V2 + "/modules/%d" % mid, **self.h_pdt)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Module.objects.count(), 0)

    def test_khong_xoa_duoc_mo_dun_dang_co_buoi_hoc(self):
        """Xoá mô-đun đang dùng sẽ kéo theo mất buổi học — phải chặn."""
        mid = self._mk().json()["id"]
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="college"
        )
        Session.objects.create(
            tenant=self.tenant, module_id=mid, student_group=g,
            session_type="theory", tier="vocational",
        )
        r = self.c.delete(V2 + "/modules/%d" % mid, **self.h_pdt)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Module.objects.count(), 1)

    def test_loc_theo_nhom_va_tim_kiem(self):
        g = StudentGroup.objects.create(
            tenant=self.tenant, code="11A3", name="11A3",
            enrollment_type="dual_degree",
        )
        self._mk("MD01", student_group_id=g.id)
        self._mk("MD02", name="Hàn cơ bản")
        rows = self.c.get(V2 + "/modules?group=11A3", **self.h_pdt).json()
        self.assertEqual([m["code"] for m in rows], ["MD01"])
        rows = self.c.get(V2 + "/modules?q=hàn", **self.h_pdt).json()
        self.assertEqual([m["code"] for m in rows], ["MD02"])

    def test_giao_vien_khong_duoc_tao_mo_dun(self):
        r = self._mk_as_gv()
        self.assertEqual(r.status_code, 403)

    def _mk_as_gv(self):
        return self.post(
            V2 + "/modules", {"code": "X", "name": "X"}, self.h_gv
        )

    def test_khong_thay_mo_dun_truong_khac(self):
        khac = Tenant.objects.create(code="X", name="X")
        Module.objects.create(tenant=khac, code="ZZ", name="Z")
        rows = self.c.get(V2 + "/modules", **self.h_pdt).json()
        self.assertEqual(rows, [])


class ProgramReportTests(ApiBase):
    """FR-9.6: tỉ lệ thực hành theo chương trình so với ngưỡng quy định."""

    def _group(self, code, loai, size=30):
        return StudentGroup.objects.create(
            tenant=self.tenant, code=code, name=code,
            enrollment_type=loai, size=size,
        )

    def _mod(self, code, g, lt, th):
        return Module.objects.create(
            tenant=self.tenant, code=code, name=code,
            theory_hours=lt, practice_hours=th, student_group=g,
        )

    def test_ti_le_dat_nguong(self):
        g = self._group("CD1", "college")
        self._mod("M1", g, 40, 60)  # TH 60% -> trong khoảng 50-70
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "college"][0]
        self.assertEqual(row["practice_pct"], 60.0)
        self.assertEqual(row["status"], "dat")

    def test_thieu_thuc_hanh_bi_canh_bao(self):
        g = self._group("CD2", "college")
        self._mod("M2", g, 80, 20)  # TH 20% -> dưới 50
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "college"][0]
        self.assertEqual(row["status"], "thieu_thuc_hanh")

    def test_thua_thuc_hanh_bi_canh_bao(self):
        g = self._group("TC1", "intermediate")
        self._mod("M3", g, 5, 95)  # TH 95% -> trên 75
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "intermediate"][0]
        self.assertEqual(row["status"], "thua_thuc_hanh")

    def test_chua_khai_gio_thi_khong_bao_lech_chuan(self):
        self._group("SB1", "dual_degree")
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "dual_degree"][0]
        self.assertEqual(row["status"], "chua_khai_gio")
        self.assertEqual(row["total_hours"], 0)

    def test_nguong_lay_tu_cau_hinh_don_vi(self):
        """SRS §2.5 cấm mã hoá cứng ngưỡng vì thông tư sắp ban hành lại."""
        g = self._group("CD3", "college")
        self._mod("M4", g, 80, 20)
        self.tenant.config_json = {
            "practice_ratio": {"college": {"min": 10, "max": 90}}
        }
        self.tenant.save(update_fields=["config_json"])
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "college"][0]
        self.assertEqual(row["status"], "dat")
        self.assertEqual(row["min_pct"], 10)

    def test_thu_tu_trung_cap_truoc_song_bang(self):
        self._group("SB2", "dual_degree")
        self._group("TC2", "intermediate")
        self._group("CD4", "college")
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        self.assertEqual(
            [r["program"] for r in rows["programs"]],
            ["college", "intermediate", "dual_degree"],
        )

    def test_dem_dung_so_nhom_va_hoc_sinh(self):
        self._group("CD5", "college", size=30)
        self._group("CD6", "college", size=25)
        rows = self.c.get(V2 + "/reports/programs", **self.h_pdt).json()
        row = [r for r in rows["programs"] if r["program"] == "college"][0]
        self.assertEqual(row["group_count"], 2)
        self.assertEqual(row["student_count"], 55)


class PortalTests(ApiBase):
    """FR-8.4: cổng xem lịch riêng cho giáo viên và sinh viên."""

    def setUp(self):
        super().setUp()
        self.gv_ho_so = Teacher.objects.create(
            tenant=self.tenant, code="GV01", name="Trần Thị Bích"
        )
        self.gv.teacher = self.gv_ho_so
        self.gv.save(update_fields=["teacher"])
        self.gv_khac = Teacher.objects.create(
            tenant=self.tenant, code="GV02", name="Lê Văn Cường"
        )
        self.sch = Schedule.objects.create(
            tenant=self.tenant, name="HK1", status="published"
        )
        self.grp = StudentGroup.objects.create(
            tenant=self.tenant, code="11A3", name="11A3",
            enrollment_type="dual_degree",
        )
        self.mod = Module.objects.create(
            tenant=self.tenant, code="MD01", name="Kỹ thuật điện"
        )

    def _buoi(self, teacher, day=0, period=0, **kw):
        kw.setdefault("session_type", "theory")
        s = Session.objects.create(
            tenant=self.tenant, schedule=self.sch, module=self.mod,
            student_group=self.grp, tier="vocational",
            assigned_timeslot={"day": day, "period": period}, **kw
        )
        if teacher:
            s.assigned_teachers.add(teacher)
        return s

    def test_giao_vien_chi_thay_buoi_cua_minh(self):
        self._buoi(self.gv_ho_so, day=0)
        self._buoi(self.gv_khac, day=1)
        r = self.c.get(V2 + "/me/schedule", **self.h_gv).json()
        self.assertEqual(len(r["sessions"]), 1)
        self.assertEqual(r["sessions"][0]["day"], 0)
        self.assertEqual(r["teacher_code"], "GV01")

    def test_giao_vien_khong_thay_lich_chua_xuat_ban(self):
        """Dạy theo bản nháp là sai; chỉ bản đã chốt mới hiện."""
        self.sch.status = "solved"
        self.sch.save(update_fields=["status"])
        self._buoi(self.gv_ho_so)
        r = self.c.get(V2 + "/me/schedule", **self.h_gv).json()
        self.assertEqual(r["sessions"], [])
        self.assertIsNone(r["schedule_id"])

    def test_can_bo_dao_tao_xem_duoc_ban_nhap(self):
        self.sch.status = "solved"
        self.sch.save(update_fields=["status"])
        self._buoi(self.gv_ho_so)
        r = self.c.get(V2 + "/me/schedule", **self.h_pdt).json()
        self.assertEqual(r["schedule_id"], self.sch.id)
        self.assertFalse(r["published"])

    def test_tai_khoan_chua_gan_ho_so_giao_vien(self):
        self.gv.teacher = None
        self.gv.save(update_fields=["teacher"])
        r = self.c.get(V2 + "/me/schedule", **self.h_gv).json()
        self.assertEqual(r["sessions"], [])
        self.assertIn("hồ sơ giáo viên", r["detail"])

    def test_sinh_vien_phai_chon_nhom(self):
        sv = User.objects.create(
            tenant=self.tenant, email="sv@cuwc.edu.vn", name="SV",
            password_hash=hash_password("x"), role="student",
        )
        h = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(sv)}
        r = self.c.get(V2 + "/me/schedule", **h).json()
        self.assertEqual(r["sessions"], [])
        self.assertIn("chọn nhóm nghề", r["detail"])

    def test_sinh_vien_xem_lich_nhom_cua_minh(self):
        sv = User.objects.create(
            tenant=self.tenant, email="sv2@cuwc.edu.vn", name="SV2",
            password_hash=hash_password("x"), role="student",
        )
        h = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(sv)}
        self._buoi(self.gv_ho_so)
        r = self.c.get(V2 + "/me/schedule?group=11A3", **h).json()
        self.assertEqual(len(r["sessions"]), 1)
        self.assertEqual(r["group_code"], "11A3")

    def test_buoi_co_du_thong_tin_de_hien_thi(self):
        self._buoi(self.gv_ho_so)
        r = self.c.get(V2 + "/me/schedule", **self.h_gv).json()
        s = r["sessions"][0]
        for k in ("module_name", "group_code", "shift", "duration_slots"):
            self.assertIn(k, s)
        self.assertEqual(s["teachers"], ["Trần Thị Bích"])

    def test_khong_thay_lich_truong_khac(self):
        khac = Tenant.objects.create(code="X", name="X")
        sch = Schedule.objects.create(
            tenant=khac, name="HK1", status="published"
        )
        r = self.c.get(
            V2 + "/me/schedule?schedule_id=%d" % sch.id, **self.h_gv
        ).json()
        self.assertIsNone(r["schedule_id"])

    def test_tai_giang_day_cua_chinh_minh(self):
        self._buoi(self.gv_ho_so, duration_slots=2)
        self._buoi(self.gv_ho_so, day=1, session_type="practice",
                   duration_slots=4)
        r = self.c.get(V2 + "/me/workload", **self.h_gv).json()
        self.assertEqual(r["theory_periods"], 2)
        self.assertEqual(r["practice_periods"], 4)
        # 2 tiết LT + 4 tiết TH * 0,75 = 5,0 giờ chuẩn
        self.assertEqual(r["standard_hours"], 5.0)

    def test_khong_co_ho_so_thi_khong_co_tai_giang_day(self):
        self.gv.teacher = None
        self.gv.save(update_fields=["teacher"])
        r = self.c.get(V2 + "/me/workload", **self.h_gv)
        self.assertEqual(r.status_code, 400)


class ConflictOverlapTests(ApiBase):
    """FR-7.11: phát hiện xung đột phải tính cả độ dài buổi học."""

    def setUp(self):
        super().setUp()
        self.sch = Schedule.objects.create(tenant=self.tenant, name="HK1")
        self.gv1 = Teacher.objects.create(
            tenant=self.tenant, code="GV01", name="A"
        )
        self.mod = Module.objects.create(
            tenant=self.tenant, code="MD01", name="M"
        )
        self.g1 = StudentGroup.objects.create(
            tenant=self.tenant, code="G1", name="G1",
            enrollment_type="college",
        )
        self.g2 = StudentGroup.objects.create(
            tenant=self.tenant, code="G2", name="G2",
            enrollment_type="college",
        )

    def _buoi(self, group, period, slots, teacher=None, room=None):
        s = Session.objects.create(
            tenant=self.tenant, schedule=self.sch, module=self.mod,
            student_group=group, session_type="practice", tier="vocational",
            duration_slots=slots, assigned_resource=room,
            assigned_timeslot={"day": 0, "period": period},
        )
        if teacher:
            s.assigned_teachers.add(teacher)
        return s

    def _conflicts(self):
        r = self.c.get(
            "/api/schedule/%d/conflicts" % self.sch.id, **self.h_pdt
        )
        self.assertEqual(r.status_code, 200)
        return r.json()["conflicts"]

    def test_buoi_dai_chong_lan_bi_phat_hien(self):
        """GV dạy tiết 1 kéo 4 tiết, buổi kia bắt đầu tiết 3 -> phải báo."""
        self._buoi(self.g1, 0, 4, teacher=self.gv1)
        self._buoi(self.g2, 2, 1, teacher=self.gv1)
        c = self._conflicts()
        self.assertTrue(c, "chồng lấn giữa chừng phải bị phát hiện")
        self.assertEqual(c[0]["type"], "teacher")

    def test_khong_bao_nham_khi_khong_chong_lan(self):
        self._buoi(self.g1, 0, 2, teacher=self.gv1)
        self._buoi(self.g2, 2, 2, teacher=self.gv1)
        self.assertEqual(self._conflicts(), [])

    def test_moi_cap_chi_bao_mot_lan(self):
        """Chồng lấn 3 tiết vẫn chỉ là một xung đột, không phải ba."""
        self._buoi(self.g1, 0, 4, teacher=self.gv1)
        self._buoi(self.g2, 1, 3, teacher=self.gv1)
        c = [x for x in self._conflicts() if x["type"] == "teacher"]
        self.assertEqual(len(c), 1)

    def test_phong_bi_trung_khi_buoi_dai_chong_lan(self):
        from scheduler.models import Resource

        room = Resource.objects.create(
            tenant=self.tenant, code="A11-204", name="X", type="workshop",
            quantity=1, available_quantity=1,
        )
        self._buoi(self.g1, 0, 3, room=room)
        self._buoi(self.g2, 2, 2, room=room)
        kinds = {x["type"] for x in self._conflicts()}
        self.assertIn("room", kinds)

    def test_ten_ngay_van_dung(self):
        self._buoi(self.g1, 0, 4, teacher=self.gv1)
        self._buoi(self.g2, 2, 1, teacher=self.gv1)
        self.assertEqual(self._conflicts()[0]["day_name"], "Thứ 2")


class SwapCandidateTests(ApiBase):
    """FR-7.8 và FR-7.12: gợi ý ô đổi được, tô màu theo bảng màu bắt buộc."""

    def setUp(self):
        super().setUp()
        self.sch = Schedule.objects.create(tenant=self.tenant, name="HK1")
        self.gv1 = Teacher.objects.create(
            tenant=self.tenant, code="GV01", name="A"
        )
        self.gv2 = Teacher.objects.create(
            tenant=self.tenant, code="GV02", name="B"
        )
        self.mod = Module.objects.create(
            tenant=self.tenant, code="MD01", name="M"
        )
        self.g1 = StudentGroup.objects.create(
            tenant=self.tenant, code="G1", name="G1",
            enrollment_type="college",
        )
        self.g2 = StudentGroup.objects.create(
            tenant=self.tenant, code="G2", name="G2",
            enrollment_type="college",
        )

    def _buoi(self, group, day, period, slots=1, teacher=None, **kw):
        s = Session.objects.create(
            tenant=self.tenant, schedule=self.sch, module=self.mod,
            student_group=group, session_type="theory", tier="vocational",
            duration_slots=slots,
            assigned_timeslot={"day": day, "period": period}, **kw
        )
        if teacher:
            s.assigned_teachers.add(teacher)
        return s

    def _cands(self, sid, scope="group"):
        r = self.c.get(
            V2 + "/schedule/%d/swap-candidates/%d?scope=%s"
            % (self.sch.id, sid, scope),
            **self.h_pdt
        )
        self.assertEqual(r.status_code, 200)
        return r.json()

    def test_o_trong_lich_duoc_cham_mau_xanh(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._buoi(self.g1, 1, 0, teacher=self.gv1)
        r = self._cands(a.id)
        self.assertEqual(len(r["candidates"]), 1)
        self.assertEqual(r["candidates"][0]["verdict"], "green")
        self.assertEqual(r["green_count"], 1)

    def test_trung_giao_vien_bi_cham_hong_dam(self):
        """GV1 đã có tiết ở chỗ đích -> chặn hẳn."""
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 1, 0, teacher=self.gv2)
        # GV1 bận đúng ô đích
        self._buoi(self.g2, 1, 0, teacher=self.gv1)
        r = self._cands(a.id, scope="all")
        row = [c for c in r["candidates"] if c["session_id"] == b.id][0]
        self.assertEqual(row["verdict"], "pink_dark")
        self.assertIn("giáo viên bận", row["reason"])

    def test_khac_so_tiet_bi_cham_hong_nhat(self):
        a = self._buoi(self.g1, 0, 0, slots=1, teacher=self.gv1)
        self._buoi(self.g1, 1, 0, slots=3, teacher=self.gv1)
        r = self._cands(a.id)
        self.assertEqual(r["candidates"][0]["verdict"], "pink")

    def test_an_mat_ngay_nghi_bi_cham_da_cam(self):
        """GV khai nghỉ 5/6 ngày; đẩy sang ngày mới là vi phạm hạn chế."""
        self.gv1.days_off_per_week = 5
        self.gv1.save(update_fields=["days_off_per_week"])
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._buoi(self.g1, 3, 0, teacher=self.gv2)
        r = self._cands(a.id)
        self.assertEqual(r["candidates"][0]["verdict"], "orange")

    def test_pham_vi_nhom_va_toan_truong_khac_nhau(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._buoi(self.g2, 1, 0, teacher=self.gv2)
        self.assertEqual(len(self._cands(a.id, "group")["candidates"]), 0)
        self.assertEqual(len(self._cands(a.id, "all")["candidates"]), 1)

    def test_buoi_da_ghim_khong_doi_duoc(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1, is_pinned=True)
        r = self.c.get(
            V2 + "/schedule/%d/swap-candidates/%d" % (self.sch.id, a.id),
            **self.h_pdt
        )
        self.assertEqual(r.status_code, 400)

    def test_buoi_ghim_khong_hien_trong_danh_sach_dich(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._buoi(self.g1, 1, 0, teacher=self.gv2, is_locked=True)
        self.assertEqual(self._cands(a.id)["candidates"], [])


class SwapExecuteTests(SwapCandidateTests):
    def _swap(self, a, b, headers=None):
        return self.post(
            V2 + "/schedule/%d/swap" % self.sch.id,
            {"session_id": a.id, "other_id": b.id},
            headers or self.h_pdt,
        )

    def test_doi_cho_thanh_cong(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 2, 3, teacher=self.gv1)
        r = self._swap(a, b)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["swapped"])
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual(a.assigned_timeslot["day"], 2)
        self.assertEqual(a.assigned_timeslot["period"], 3)
        self.assertEqual(b.assigned_timeslot["day"], 0)

    def test_danh_dau_lich_da_sua_tay(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 1, 0, teacher=self.gv1)
        self._swap(a, b)
        self.sch.refresh_from_db()
        self.assertTrue(self.sch.is_manual_edit)

    def test_tu_choi_khi_trung_tiet(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g2, 1, 0, teacher=self.gv2)
        # GV1 bận sẵn ở ô đích của a
        self._buoi(self.g2, 1, 0, teacher=self.gv1)
        r = self._swap(a, b)
        self.assertEqual(r.status_code, 409)
        a.refresh_from_db()
        self.assertEqual(a.assigned_timeslot["day"], 0, "không được đổi")

    def test_giao_vien_khong_duoc_doi_cho(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 1, 0, teacher=self.gv1)
        self.assertEqual(self._swap(a, b, self.h_gv).status_code, 403)

    def test_khong_doi_buoi_da_khoa(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 1, 0, teacher=self.gv1, is_locked=True)
        self.assertEqual(self._swap(a, b).status_code, 400)

    def test_khong_doi_voi_chinh_no(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self.assertEqual(self._swap(a, a).status_code, 400)

    def test_buoi_chua_xep_tiet_thi_khong_doi_duoc(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = Session.objects.create(
            tenant=self.tenant, schedule=self.sch, module=self.mod,
            student_group=self.g1, session_type="theory", tier="vocational",
        )
        self.assertEqual(self._swap(a, b).status_code, 400)

    def test_khong_doi_duoc_buoi_cua_truong_khac(self):
        khac = Tenant.objects.create(code="X", name="X")
        sch = Schedule.objects.create(tenant=khac, name="HK1")
        r = self.post(
            V2 + "/schedule/%d/swap" % sch.id,
            {"session_id": 1, "other_id": 2},
            self.h_pdt,
        )
        self.assertEqual(r.status_code, 404)


class TrayTests(SwapCandidateTests):
    """FR-7.9: khay tiết chờ — gỡ ra, để đó, thả lại vào ô trống."""

    def _tray(self):
        r = self.c.get(V2 + "/schedule/%d/tray" % self.sch.id, **self.h_pdt)
        self.assertEqual(r.status_code, 200)
        return r.json()

    def _push(self, s, headers=None):
        return self.post(
            V2 + "/schedule/%d/tray" % self.sch.id,
            {"session_id": s.id},
            headers or self.h_pdt,
        )

    def _place(self, s, day, period, headers=None):
        return self.post(
            V2 + "/schedule/%d/tray/place" % self.sch.id,
            {"session_id": s.id, "day": day, "period": period},
            headers or self.h_pdt,
        )

    def test_go_buoi_ra_khay(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        r = self._push(a)
        self.assertEqual(r.status_code, 200)
        a.refresh_from_db()
        self.assertIsNone(a.assigned_timeslot)
        self.assertEqual(self._tray()["count"], 1)

    def test_khay_chi_chua_buoi_chua_xep(self):
        self._buoi(self.g1, 0, 0, teacher=self.gv1)
        b = self._buoi(self.g1, 1, 0, teacher=self.gv1)
        self._push(b)
        t = self._tray()
        self.assertEqual(t["count"], 1)
        self.assertEqual(t["tray"][0]["session_id"], b.id)

    def test_tha_vao_o_trong(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._push(a)
        r = self._place(a, 2, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["verdict"], "green")
        a.refresh_from_db()
        self.assertEqual(a.assigned_timeslot, {"day": 2, "period": 1})
        self.assertEqual(self._tray()["count"], 0)

    def test_khong_tha_duoc_vao_o_da_co_nguoi(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._buoi(self.g2, 3, 0, teacher=self.gv1)
        self._push(a)
        r = self._place(a, 3, 0)
        self.assertEqual(r.status_code, 409)
        a.refresh_from_db()
        self.assertIsNone(a.assigned_timeslot, "thất bại thì phải giữ nguyên")

    def test_buoi_dai_khong_tran_qua_cuoi_ngay(self):
        """Buổi 3 tiết không thể bắt đầu ở tiết cuối cùng."""
        a = self._buoi(self.g1, 0, 0, slots=3, teacher=self.gv1)
        self._push(a)
        r = self._place(a, 1, 4)
        self.assertEqual(r.status_code, 400)

    def test_ngay_ngoai_khung_bi_tu_choi(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._push(a)
        self.assertEqual(self._place(a, 99, 0).status_code, 400)
        self.assertEqual(self._place(a, 0, -1).status_code, 400)

    def test_buoi_ghim_khong_go_ra_khay_duoc(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1, is_pinned=True)
        self.assertEqual(self._push(a).status_code, 400)

    def test_giao_vien_khong_duoc_go_hay_tha(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self.assertEqual(self._push(a, self.h_gv).status_code, 403)
        self.assertEqual(self._place(a, 1, 0, self.h_gv).status_code, 403)

    def test_go_hai_lan_khong_bao_loi(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._push(a)
        r = self._push(a)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["in_tray"])

    def test_thao_tac_khay_danh_dau_sua_tay(self):
        a = self._buoi(self.g1, 0, 0, teacher=self.gv1)
        self._push(a)
        self.sch.refresh_from_db()
        self.assertTrue(self.sch.is_manual_edit)
