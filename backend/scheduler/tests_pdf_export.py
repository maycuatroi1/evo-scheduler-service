"""Kiểm chứng bản xuất PDF theo mẫu bản in của trường (FR-8.2, SRS §9)."""

import datetime
import re
import zlib

from django.test import Client, TestCase

from scheduler import pdf_export
from scheduler.accounts import hash_password, mint_token
from scheduler.models import (
    Module,
    Resource,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    Tenant,
    User,
)


def pdf_text(data):
    """Rút chữ trong PDF để kiểm tra dấu tiếng Việt còn nguyên."""
    from pypdf import PdfReader
    import io as _io

    reader = PdfReader(_io.BytesIO(data))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


class PdfBase(TestCase):
    def setUp(self):
        self.t = Tenant.objects.create(
            code="CUWC", name="CĐ Xây dựng Công trình Đô thị"
        )
        self.sch = Schedule.objects.create(
            tenant=self.t,
            name="TKB nghề khối 11",
            week_number=3,
            week_start=datetime.date(2026, 8, 24),
        )
        self.room = Resource.objects.create(
            tenant=self.t, code="A11-204", name="Xưởng điện",
            type="workshop", quantity=1, available_quantity=1,
        )
        self.gv = Teacher.objects.create(
            tenant=self.t, code="GV1", name="Nguyễn Văn Ổn"
        )
        self.mod = Module.objects.create(
            tenant=self.t, code="MD01", name="Kỹ thuật điện ứng dụng"
        )

    def _group(self, code="11A3", size=16, nghe="CNKT điều khiển tự động"):
        return StudentGroup.objects.create(
            tenant=self.t, code=code, name=code,
            enrollment_type="dual_degree", size=size, occupation=nghe,
        )

    def _session(self, group, day=0, period=0, slots=2, **kw):
        kw.setdefault("session_type", "practice")
        kw.setdefault("tier", "vocational")
        kw.setdefault("assigned_resource", self.room)
        s = Session.objects.create(
            tenant=self.t, schedule=self.sch, module=self.mod,
            student_group=group, duration_slots=slots,
            assigned_timeslot={"day": day, "period": period}, **kw
        )
        s.assigned_teachers.add(self.gv)
        return s


class PdfLayoutTests(PdfBase):
    def test_xuat_duoc_pdf_hop_le(self):
        self._session(self._group())
        data = pdf_export.build_pdf(self.t, self.sch)
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 2000)

    def test_chu_tieng_viet_khong_mat_dau(self):
        """NFR-5: phông dựng sẵn của reportlab không có dấu nên phải nhúng."""
        self._session(self._group())
        text = pdf_text(pdf_export.build_pdf(self.t, self.sch))
        for chuoi in [
            "Kỹ thuật điện ứng dụng",
            "Nguyễn Văn Ổn",
            "CĐ XÂY DỰNG CÔNG TRÌNH ĐÔ THỊ",
            "THỨ",
            "BUỔI",
            "TIẾT",
        ]:
            self.assertIn(chuoi, text, "mất dấu hoặc thiếu: " + chuoi)

    def test_phong_chu_duoc_nhung_vao_file(self):
        """Không nhúng thì máy in thiếu phông sẽ ra ô vuông."""
        self._session(self._group())
        data = pdf_export.build_pdf(self.t, self.sch)
        self.assertIn(b"/FontFile2", data)
        self.assertIn(b"SourceSans3", data)

    def test_dau_cot_ghi_nghe_ma_lop_va_si_so(self):
        """Mẫu trường: "CNKT ĐIỀU KHIỂN TỰ ĐỘNG (11A3) 16"."""
        self._session(self._group(code="11A3", size=16))
        text = pdf_text(pdf_export.build_pdf(self.t, self.sch))
        self.assertIn("(11A3)", text)
        self.assertIn("16", text)
        self.assertIn("CNKT ĐIỀU KHIỂN TỰ ĐỘNG", text)

    def test_ma_phong_co_mat_tren_ban_in(self):
        self._session(self._group())
        text = pdf_text(pdf_export.build_pdf(self.t, self.sch))
        self.assertIn("A11-204", text)

    def test_truc_doc_co_du_thu_buoi_tiet(self):
        g = self._group()
        self._session(g, day=0, period=0, slots=1)
        # morning_count=2 nên tiết 3 thuộc buổi chiều
        self._session(g, day=0, period=3, slots=1)
        text = pdf_text(pdf_export.build_pdf(self.t, self.sch, morning_count=2))
        self.assertIn("Sáng", text)
        self.assertIn("Chiều", text)
        self.assertIn("Thứ 2", text)

    def test_lich_rong_van_ra_pdf_khong_vo(self):
        data = pdf_export.build_pdf(self.t, self.sch)
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn("chưa có buổi nào", pdf_text(data))


class PdfMergeTests(PdfBase):
    def test_buoi_nhieu_tiet_duoc_gop_o(self):
        """Mô-đun 2 tiết liền phải gộp, không lặp tên hai lần."""
        self._session(self._group(), period=0, slots=2)
        grid, groups, days, periods = pdf_export.collect(
            self.t, self.sch, morning_count=2
        )
        st = pdf_export._styles()
        rows, spans, extra, cols = pdf_export.build_table(
            grid, groups, days, periods, 2, st
        )
        merges = [s for s in spans if s[1][0] >= 3]
        self.assertTrue(merges, "phải có ít nhất một ô gộp cho buổi 2 tiết")

    def test_khong_gop_tran_sang_buoi_khac(self):
        """Buổi bắt đầu tiết cuối buổi sáng không được tràn xuống buổi chiều."""
        # morning_count=2: tiết 1 là index 1, tiết 3 (index 2) đã là chiều
        self._session(self._group(), period=1, slots=3)
        grid, groups, days, periods = pdf_export.collect(
            self.t, self.sch, morning_count=2
        )
        occupied = [k for k in grid if k[1] >= 2]
        self.assertEqual(
            occupied, [], "buổi sáng không được lấn sang tiết buổi chiều"
        )

    def test_hai_lop_thanh_hai_cot_rieng(self):
        self._session(self._group(code="11A3"))
        self._session(self._group(code="11A11", nghe="Điện công nghiệp"))
        grid, groups, days, periods = pdf_export.collect(
            self.t, self.sch, morning_count=2
        )
        self.assertEqual(len(groups), 2)
        text = pdf_text(pdf_export.build_pdf(self.t, self.sch))
        self.assertIn("(11A3)", text)
        self.assertIn("(11A11)", text)


class PdfApiTests(PdfBase):
    def setUp(self):
        super().setUp()
        self.c = Client()
        self.user = User.objects.create(
            tenant=self.t, email="pdt@cuwc.edu.vn", name="PDT",
            password_hash=hash_password("x"), role="registrar",
        )
        self.h = {"HTTP_AUTHORIZATION": "Bearer " + mint_token(self.user)}

    def test_endpoint_tra_ve_pdf(self):
        self._session(self._group())
        r = self.c.get(
            "/api/schedule/%s/export?format=pdf" % self.sch.id, **self.h
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertIn(".pdf", r["Content-Disposition"])
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_mac_dinh_van_la_excel(self):
        r = self.c.get("/api/schedule/%s/export" % self.sch.id, **self.h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("spreadsheet", r["Content-Type"])

    def test_dinh_dang_la_bi_tu_choi(self):
        r = self.c.get(
            "/api/schedule/%s/export?format=docx" % self.sch.id, **self.h
        )
        self.assertEqual(r.status_code, 400)

    def test_khong_xem_duoc_lich_truong_khac(self):
        khac = Tenant.objects.create(code="X", name="X")
        sch = Schedule.objects.create(tenant=khac, name="TKB")
        r = self.c.get(
            "/api/schedule/%s/export?format=pdf" % sch.id, **self.h
        )
        self.assertEqual(r.status_code, 404)
