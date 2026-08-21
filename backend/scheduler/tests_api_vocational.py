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
