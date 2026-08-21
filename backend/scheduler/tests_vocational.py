"""Kiểm chứng các ràng buộc đặc thù trường nghề bằng dữ liệu thật của CUWC.

Chạy: python manage.py test scheduler.tests_vocational
"""

from django.test import TestCase

from scheduler.models import (
    ConstraintRule,
    HomeroomClass,
    Module,
    Resource,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    TeacherModule,
    Tenant,
    User,
)
from scheduler.solver import engine


def _horizon(days=5, periods=10, morning=5):
    out, i = [], 0
    for d in range(days):
        for p in range(periods):
            out.append(
                {
                    "index": i,
                    "week": 0,
                    "day": d,
                    "period": p,
                    "day_name": "d%d" % d,
                    "is_morning": p < morning,
                }
            )
            i += 1
    return out


class VocationalConstraintTests(TestCase):
    """Bốn ràng buộc mới, mỗi cái một tình huống có thật trên TKB."""

    def setUp(self):
        self.tenant = Tenant.objects.create(code="CUWC", name="CUWC")
        self.room = Resource.objects.create(
            tenant=self.tenant,
            code="A11-204",
            name="Xuong dien",
            type="workshop",
            capacity=0,
            quantity=1,
            available_quantity=1,
        )

    def _data(self, sessions, horizon=None):
        return {
            "tenant_code": "CUWC",
            "horizon": horizon or _horizon(),
            "sessions": sessions,
            "resources": [
                {
                    "id": self.room.id,
                    "code": self.room.code,
                    "type": "workshop",
                    "capacity": 0,
                    "quantity": 1,
                    "available_quantity": 1,
                }
            ],
            "teachers": [],
            "rules": [],
            "hours_per_slot": 1.0,
            "teacher_module_map": {},
        }

    def _session(self, sid, code, **kw):
        base = {
            "id": sid,
            "code": code,
            "session_type": "practice",
            "tier": "vocational",
            "duration_slots": 1,
            "group_size": 16,
            "group_code": code,
            "module_code": "MD" + str(sid),
            "teacher_codes": [],
            "is_locked": False,
            "assigned_timeslot": None,
            "assigned_resource_code": None,
            "homeroom_codes": [],
            "allowed_shift": "any",
            "hazardous": False,
            "consumes_resources": True,
        }
        base.update(kw)
        return base

    # ---------- group_same_class ----------

    def test_nhom_cung_lop_van_hoa_khong_trung_gio(self):
        """11A3 tách ba nhóm nghề — ba nhóm không được học cùng tiết."""
        sessions = [
            self._session(1, "G1", homeroom_codes=["11A3"]),
            self._session(2, "G4", homeroom_codes=["11A3"]),
            self._session(3, "G5", homeroom_codes=["11A3"]),
        ]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -103, "type": "group_same_class", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        slots = [a.timeslot_index for a in res.assignments]
        self.assertEqual(
            len(set(slots)), 3, "Ba nhóm cùng lớp 11A3 phải ở ba tiết khác nhau"
        )

    def test_nhieu_lop_gop_mot_nhom_chan_moi_lop_thanh_vien(self):
        """12A1+12A4 gộp một nhóm; nhóm ấy chặn cả hai lớp."""
        sessions = [
            self._session(1, "M3", homeroom_codes=["12A1", "12A4"]),
            self._session(2, "M5", homeroom_codes=["12A1"]),
            self._session(3, "M9", homeroom_codes=["12A4"]),
        ]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -103, "type": "group_same_class", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        slots = [a.timeslot_index for a in res.assignments]
        self.assertEqual(
            len(set(slots)), 3, "Nhóm gộp phải loại trừ cả hai lớp thành viên"
        )

    # ---------- shift_by_grade ----------

    def test_buoi_van_hoa_khoi_11_phai_o_buoi_chieu(self):
        """Khối 11 học văn hoá buổi chiều — không được rơi vào tiết sáng."""
        sessions = [
            self._session(
                1, "V1", session_type="theory", tier="culture", allowed_shift="afternoon"
            )
        ]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -104, "type": "shift_by_grade", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        period = res.assignments[0].period
        self.assertGreaterEqual(
            period, 5, "Tiết văn hoá khối 11 phải nằm ở buổi chiều"
        )

    def test_buoi_nghe_khoi_11_phai_o_buoi_sang(self):
        """Ca nghề là phần bù của ca văn hoá."""
        sessions = [self._session(1, "G1", allowed_shift="morning")]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -104, "type": "shift_by_grade", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        period = res.assignments[0].period
        self.assertLess(period, 5, "Buổi nghề khối 11 phải nằm ở buổi sáng")

    # ---------- capacity_by_type ----------

    def test_canh_bao_khi_nhom_thuc_hanh_vuot_tran(self):
        """Nhóm 38 HS vào xưởng, trần thực hành là 18."""
        sessions = [self._session(1, "G3", group_size=38)]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -106, "type": "capacity_by_type", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertTrue(
            any("vượt trần" in w for w in res.violations),
            "Phải cảnh báo nhóm vượt trần sĩ số thực hành",
        )

    def test_nghe_doc_hai_ap_tran_10(self):
        sessions = [self._session(1, "G7", group_size=14, hazardous=True)]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -106, "type": "capacity_by_type", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertTrue(
            any("vượt trần 10" in w for w in res.violations),
            "Nghề nặng nhọc độc hại phải áp trần 10",
        )

    def test_khong_canh_bao_khi_trong_tran(self):
        sessions = [self._session(1, "G1", group_size=16)]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -106, "type": "capacity_by_type", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertFalse(any("vượt trần" in w for w in res.violations))

    # ---------- offsite_no_room ----------

    def test_tuan_thuc_tap_khong_chiem_phong(self):
        """Thực tập tại doanh nghiệp: chặn lớp nhưng không tốn phòng."""
        sessions = [
            self._session(
                1, "C1", session_type="internship", consumes_resources=False
            )
        ]
        data = self._data(sessions)
        data["rules"] = [
            {"id": -105, "type": "offsite_no_room", "hardness": "hard", "weight": 1}
        ]
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        self.assertIsNone(
            res.assignments[0].resource_code,
            "Buổi thực tập không được gắn phòng của trường",
        )


class ModelBehaviourTests(TestCase):
    """Các phương thức nghiệp vụ trên model."""

    def setUp(self):
        self.tenant = Tenant.objects.create(code="T", name="T")

    def test_ca_nghe_la_phan_bu_cua_ca_van_hoa(self):
        cases = [("morning", "afternoon"), ("afternoon", "morning"), ("full_day", "afternoon")]
        for culture, expected in cases:
            h = HomeroomClass.objects.create(
                tenant=self.tenant, code="X" + culture, culture_shift=culture
            )
            self.assertEqual(h.vocational_shift(), expected)

    def test_phan_quyen_theo_vai_tro(self):
        gv = User.objects.create(
            tenant=self.tenant, email="gv@x.vn", name="GV", password_hash="x", role="teacher"
        )
        pdt = User.objects.create(
            tenant=self.tenant, email="pdt@x.vn", name="PDT", password_hash="x", role="registrar"
        )
        self.assertFalse(gv.can_write())
        self.assertFalse(gv.can_publish())
        self.assertTrue(pdt.can_write())
        self.assertTrue(pdt.can_solve())

    def test_trong_so_nhan_theo_do_uu_tien(self):
        cao = ConstraintRule.objects.create(
            tenant=self.tenant, type="preference", priority="high", weight=3
        )
        thap = ConstraintRule.objects.create(
            tenant=self.tenant, type="preference", priority="low", weight=3
        )
        self.assertEqual(cao.effective_weight(), 15)
        self.assertEqual(thap.effective_weight(), 3)
        self.assertGreater(cao.effective_weight(), thap.effective_weight())

    def test_buoi_ngoai_truong_khong_chiem_tai_nguyen(self):
        grp = StudentGroup.objects.create(
            tenant=self.tenant, code="G", name="G", enrollment_type="college"
        )
        mod = Module.objects.create(tenant=self.tenant, code="M", name="M")
        thuong = Session.objects.create(
            tenant=self.tenant, module=mod, student_group=grp,
            session_type="theory", tier="vocational",
        )
        thuctap = Session.objects.create(
            tenant=self.tenant, module=mod, student_group=grp,
            session_type="internship", tier="vocational",
        )
        online = Session.objects.create(
            tenant=self.tenant, module=mod, student_group=grp,
            session_type="theory", tier="vocational", location="online",
        )
        self.assertTrue(thuong.consumes_resources())
        self.assertFalse(thuctap.consumes_resources())
        self.assertFalse(online.consumes_resources())

    def test_lop_van_hoa_lien_ket_nhieu_nhom_nghe(self):
        """Dữ liệu thật: 11A3 tách ba nhóm 16/17/30."""
        lop = HomeroomClass.objects.create(
            tenant=self.tenant, code="11A3", grade=11, size=63, culture_shift="afternoon"
        )
        for code, si in [("G1", 16), ("G4", 17), ("G5", 30)]:
            g = StudentGroup.objects.create(
                tenant=self.tenant, code=code, name=code,
                enrollment_type="dual_degree", size=si,
            )
            g.homerooms.add(lop)
        self.assertEqual(lop.groups.count(), 3)
        self.assertEqual(sum(g.size for g in lop.groups.all()), 63)


class TeacherLimitTests(VocationalConstraintTests):
    """Ràng buộc cá nhân của giáo viên — trước đây khai xong không có tác dụng."""

    def _with_teacher(self, sessions, teacher):
        data = self._data(sessions)
        data["teachers"] = [teacher]
        data["rules"] = [
            {"id": -107, "type": "teacher_limits", "hardness": "soft", "weight": 3}
        ]
        return data

    def test_toi_da_tiet_moi_buoi_duoc_ap(self):
        """Giáo viên khai tối đa 2 tiết/buổi thì không dồn 4 tiết một ngày."""
        sessions = [
            self._session(i, "G%d" % i, teacher_codes=["GV1"], group_code="G%d" % i)
            for i in range(1, 5)
        ]
        data = self._with_teacher(
            sessions,
            {"id": 1, "code": "GV1", "max_periods_per_session": 2,
             "min_periods_per_session": None, "days_off_per_week": None},
        )
        res = engine.build_and_solve(data, max_time_seconds=15, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        per_day = {}
        for a in res.assignments:
            per_day[a.day] = per_day.get(a.day, 0) + 1
        self.assertLessEqual(
            max(per_day.values()), 2, "Không được vượt 2 tiết mỗi buổi"
        )

    def test_khong_khai_gi_thi_khong_rang_buoc(self):
        sessions = [
            self._session(i, "G%d" % i, teacher_codes=["GV1"], group_code="G%d" % i)
            for i in range(1, 4)
        ]
        data = self._with_teacher(
            sessions,
            {"id": 1, "code": "GV1", "max_periods_per_session": None,
             "min_periods_per_session": None, "days_off_per_week": None},
        )
        res = engine.build_and_solve(data, max_time_seconds=10, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))

    def test_so_ngay_nghi_trong_tuan(self):
        """Khai nghỉ 3 ngày thì bộ giải dồn tiết vào ít ngày hơn."""
        sessions = [
            self._session(i, "G%d" % i, teacher_codes=["GV1"], group_code="G%d" % i)
            for i in range(1, 5)
        ]
        data = self._with_teacher(
            sessions,
            {"id": 1, "code": "GV1", "max_periods_per_session": None,
             "min_periods_per_session": None, "days_off_per_week": 3},
        )
        res = engine.build_and_solve(data, max_time_seconds=15, skip_preflight=True)
        self.assertIn(res.status, ("OPTIMAL", "FEASIBLE"))
        days_used = len({a.day for a in res.assignments})
        self.assertLessEqual(days_used, 3, "Nghỉ 3/5 ngày nên dạy tối đa 2–3 ngày")

    def test_rang_buoc_mem_khong_lam_vo_nghiem(self):
        """Ép cứng sẽ vô nghiệm; đây là ràng buộc mềm nên vẫn ra lịch."""
        sessions = [
            self._session(i, "G%d" % i, teacher_codes=["GV1"], group_code="G%d" % i)
            for i in range(1, 11)
        ]
        data = self._with_teacher(
            sessions,
            {"id": 1, "code": "GV1", "max_periods_per_session": 1,
             "min_periods_per_session": None, "days_off_per_week": 4},
        )
        res = engine.build_and_solve(data, max_time_seconds=15, skip_preflight=True)
        self.assertIn(
            res.status, ("OPTIMAL", "FEASIBLE"),
            "Ràng buộc mềm mâu thuẫn vẫn phải ra được lịch",
        )
