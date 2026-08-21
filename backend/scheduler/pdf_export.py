"""Xuất thời khoá biểu ra PDF theo đúng mẫu bản in của trường (FR-8.2).

Bố cục lấy từ mẫu thật (SRS §9):

- Trục dọc: Thứ -> Buổi (Sáng/Chiều) -> Tiết
- Trục ngang: mỗi cột một lớp; đầu cột ghi tên nghề, mã lớp và sĩ số
- Ô dữ liệu: tên mô-đun, tên giáo viên, mã phòng in dọc ở dải hẹp bên phải
- Mô-đun chiếm nhiều tiết liền nhau thì gộp ô

Phông chữ đi kèm trong ``scheduler/fonts`` vì phông dựng sẵn của reportlab
không có dấu tiếng Việt, mà NFR-5 bắt buộc toàn bộ giao diện có dấu.
"""

import io
import os
from datetime import timedelta

from django.db.models import Q

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

FONT_BODY = "SourceSans3"
FONT_BODY_BOLD = "SourceSans3-Bold"
FONT_DISPLAY = "BarlowCondensed"

DAY_NAME_VI = {
    0: "Thứ 2",
    1: "Thứ 3",
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ nhật",
}

SESSION_TYPE_VI = {
    "theory": "LT",
    "practice": "TH",
    "internship": "TT",
    "exam": "KT",
}

# Màu lấy từ logo trường, trùng với bảng màu giao diện.
COLOR_CULTURE = colors.HexColor("#2c5c9e")
COLOR_VOCATIONAL = colors.HexColor("#8f5e0e")
COLOR_HEADER_BG = colors.HexColor("#e8edf5")
COLOR_SHIFT_BG = colors.HexColor("#f3f4f6")
COLOR_GRID = colors.HexColor("#9ca3af")
COLOR_GRID_LIGHT = colors.HexColor("#d1d5db")

_FONTS_READY = False


def _register_fonts():
    """Nạp phông một lần cho cả tiến trình; reportlab giữ sổ đăng ký toàn cục."""
    global _FONTS_READY
    if _FONTS_READY:
        return
    pairs = [
        (FONT_BODY, "SourceSans3-Regular.ttf"),
        (FONT_BODY_BOLD, "SourceSans3-Bold.ttf"),
        (FONT_DISPLAY, "BarlowCondensed-SemiBold.ttf"),
    ]
    for name, filename in pairs:
        path = os.path.join(FONT_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                "Thiếu phông %s cho bản in PDF; chữ tiếng Việt sẽ mất dấu." % path
            )
        pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        FONT_BODY, normal=FONT_BODY, bold=FONT_BODY_BOLD
    )
    _FONTS_READY = True


# --------------------------------------------------------------------------
# Thu thập dữ liệu
# --------------------------------------------------------------------------

def _column_label(group):
    """Đầu cột: tên nghề, mã lớp và sĩ số — đúng mẫu "CNKT ... (11A3) 16"."""
    nghe = (group.occupation or group.name or "").strip()
    parts = []
    if nghe:
        parts.append(nghe.upper())
    parts.append("(%s)" % group.code)
    if group.size:
        parts.append(str(group.size))
    return " ".join(parts)


def _cell_lines(session):
    """Ba dòng trong ô: mô-đun, giáo viên, loại buổi."""
    mod = session.module
    ten = (mod.name or mod.code or "").strip()
    gv = ", ".join(t.name for t in session.assigned_teachers.all())
    loai = SESSION_TYPE_VI.get(session.session_type, "")
    return ten, gv, loai


def collect(tenant, schedule, morning_count=5, group_ids=None):
    """Dựng lưới in: {(day, period, group_id): buổi} cùng danh sách cột.

    Chỉ lấy buổi đã có tiết. Buổi thực tập hay học ngoài trường vẫn hiện
    vì học sinh vẫn phải biết, dù chúng không chiếm phòng.
    """
    sessions = (
        tenant.sessions.select_related(
            "module", "student_group", "assigned_resource"
        )
        .prefetch_related("assigned_teachers", "student_group__homerooms")
    )
    if schedule is not None:
        # Buổi gắn với lịch khác thì bỏ; buổi chưa gắn lịch nào vẫn lấy để
        # bản in không rỗng với dữ liệu nhập từ Excel.
        sessions = sessions.filter(
            Q(schedule=schedule) | Q(schedule__isnull=True)
        )
    if group_ids:
        sessions = sessions.filter(student_group_id__in=group_ids)

    grid = {}
    groups = {}
    days = set()
    periods = set()
    for s in sessions:
        ts = s.assigned_timeslot or {}
        day, period = ts.get("day"), ts.get("period")
        if day is None or period is None:
            continue
        g = s.student_group
        groups[g.id] = g
        days.add(int(day))
        span = max(1, int(s.duration_slots or 1))
        for k in range(span):
            p = int(period) + k
            # Không cho buổi tràn sang buổi học kế tiếp trên bản in.
            if k and _shift_of(p, morning_count) != _shift_of(int(period), morning_count):
                break
            periods.add(p)
            grid[(int(day), p, g.id)] = (s, k, span)
    return grid, groups, sorted(days), sorted(periods)


def _shift_of(period, morning_count):
    return "morning" if period < morning_count else "afternoon"


# --------------------------------------------------------------------------
# Dựng bảng
# --------------------------------------------------------------------------

class VerticalText(Flowable):
    """Mã phòng in dọc ở dải hẹp bên phải ô, đúng như mẫu của trường.

    Vẽ thẳng lên canvas thay vì xoay một Paragraph: Paragraph xoay khiến
    reportlab tính sai chiều cao hàng và làm vỡ bố cục bảng.
    """

    def __init__(self, text, font=FONT_BODY, size=5.5, color=None):
        super().__init__()
        self.text = str(text or "")
        self.font = font
        self.size = size
        self.color = color or colors.HexColor("#6b7280")

    def wrap(self, availWidth, availHeight):
        # Bề ngang chỉ cần đủ một dòng chữ; chiều cao là bề dài chuỗi.
        self.width = self.size + 1.5
        self.height = min(
            pdfmetrics.stringWidth(self.text, self.font, self.size) + 2,
            max(availHeight, self.size),
        )
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFont(self.font, self.size)
        c.setFillColor(self.color)
        c.rotate(90)
        # Sau khi xoay, trục x chạy theo chiều cao ô nên lùi lại nửa bề ngang.
        c.drawCentredString(self.height / 2.0, -self.width + 1.0, self.text)
        c.restoreState()


def _styles():
    return {
        "title": ParagraphStyle(
            "title", fontName=FONT_DISPLAY, fontSize=15, leading=17,
            alignment=1, textColor=colors.black,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=FONT_BODY, fontSize=9, leading=11,
            alignment=1, textColor=colors.HexColor("#4b5563"),
        ),
        "colhead": ParagraphStyle(
            "colhead", fontName=FONT_BODY_BOLD, fontSize=6.5, leading=7.5,
            alignment=1,
        ),
        "module": ParagraphStyle(
            "module", fontName=FONT_BODY_BOLD, fontSize=6, leading=7,
            alignment=1,
        ),
        "teacher": ParagraphStyle(
            "teacher", fontName=FONT_BODY, fontSize=5.5, leading=6.5,
            alignment=1, textColor=colors.HexColor("#374151"),
        ),
        "room": ParagraphStyle(
            "room", fontName=FONT_BODY, fontSize=5.5, leading=6,
            alignment=1, textColor=colors.HexColor("#6b7280"),
        ),
        "axis": ParagraphStyle(
            "axis", fontName=FONT_BODY_BOLD, fontSize=7, leading=8,
            alignment=1,
        ),
    }


def _cell_flowable(session, st):
    """Nội dung một ô: mô-đun + giáo viên bên trái, mã phòng in dọc bên phải."""
    ten, gv, loai = _cell_lines(session)
    left = [Paragraph(_esc(ten), st["module"])]
    if gv:
        left.append(Paragraph(_esc(gv), st["teacher"]))
    if loai:
        left.append(Paragraph(loai, st["room"]))

    room = session.assigned_resource.code if session.assigned_resource else ""
    if not room:
        return left
    inner = Table(
        [[left, VerticalText(room)]],
        colWidths=[None, 7 * mm],
    )
    inner.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LINEBEFORE", (1, 0), (1, 0), 0.3, COLOR_GRID_LIGHT),
            ]
        )
    )
    return inner


def _esc(text):
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _title_text(schedule, tenant):
    """Dòng tiêu đề kiểu "TUẦN 03 TỪ 24/8/2026 ĐẾN 28/8/2026"."""
    ten = (schedule.name if schedule else "") or "THỜI KHOÁ BIỂU"
    if schedule is None:
        return ten.upper(), ""
    phu = ""
    if schedule.week_number:
        phu = "TUẦN %02d" % schedule.week_number
    if schedule.week_start:
        d = schedule.week_start
        het = d + timedelta(days=4)
        phu = (
            phu
            + " TỪ %d/%d/%d ĐẾN %d/%d/%d"
            % (d.day, d.month, d.year, het.day, het.month, het.year)
        ).strip()
    return ten.upper(), phu


def build_table(grid, groups, days, periods, morning_count, st):
    """Dựng bảng: hàng là Thứ/Buổi/Tiết, cột là lớp."""
    col_ids = sorted(groups, key=lambda gid: groups[gid].code)
    header = [
        Paragraph("THỨ", st["axis"]),
        Paragraph("BUỔI", st["axis"]),
        Paragraph("TIẾT", st["axis"]),
    ] + [Paragraph(_esc(_column_label(groups[gid])), st["colhead"]) for gid in col_ids]

    rows = [header]
    spans = []
    styles = []
    # Ô đã bị buổi phía trên chiếm chỗ thì để trống rồi gộp.
    covered = set()
    r = 1
    day_start = {}
    shift_start = {}
    for day in days:
        day_start[day] = r
        for shift in ("morning", "afternoon"):
            ps = [p for p in periods if _shift_of(p, morning_count) == shift]
            if not ps:
                continue
            shift_start[(day, shift)] = (r, len(ps))
            for p in ps:
                row = [
                    Paragraph(DAY_NAME_VI.get(day, "Thứ %s" % day), st["axis"]),
                    Paragraph("Sáng" if shift == "morning" else "Chiều", st["axis"]),
                    Paragraph(str(p + 1), st["axis"]),
                ]
                for c, gid in enumerate(col_ids, start=3):
                    if (day, p, gid) in covered:
                        row.append("")
                        continue
                    hit = grid.get((day, p, gid))
                    if not hit:
                        row.append("")
                        continue
                    session, offset, span = hit
                    if offset:
                        row.append("")
                        continue
                    row.append(_cell_flowable(session, st))
                    # Gộp các tiết liền nhau của cùng mô-đun.
                    reach = 0
                    for k in range(1, span):
                        if (day, p + k, gid) not in grid:
                            break
                        covered.add((day, p + k, gid))
                        reach = k
                    if reach:
                        spans.append(("SPAN", (c, r), (c, r + reach)))
                    tone = (
                        COLOR_CULTURE
                        if session.tier == "culture"
                        else COLOR_VOCATIONAL
                    )
                    styles.append(
                        ("LINEBEFORE", (c, r), (c, r + reach), 1.1, tone)
                    )
                rows.append(row)
                r += 1
        # Gộp ô "Thứ" cho cả ngày.
        if r - 1 > day_start[day]:
            spans.append(("SPAN", (0, day_start[day]), (0, r - 1)))
    for (day, shift), (start, count) in shift_start.items():
        if count > 1:
            spans.append(("SPAN", (1, start), (1, start + count - 1)))
    return rows, spans, styles, col_ids


# --------------------------------------------------------------------------
# Dựng tài liệu
# --------------------------------------------------------------------------

def build_pdf(tenant, schedule, morning_count=5, group_ids=None, page="auto"):
    """Trả về nội dung PDF dạng bytes.

    ``page="auto"`` chọn A4 khi ít lớp, A3 khi nhiều lớp, để cột không bị
    bóp quá hẹp — bản in dán bảng tin phải đọc được.
    """
    _register_fonts()
    st = _styles()
    grid, groups, days, periods = collect(
        tenant, schedule, morning_count=morning_count, group_ids=group_ids
    )

    buffer = io.BytesIO()
    ncols = len(groups)
    if page == "a3" or (page == "auto" and ncols > 8):
        pagesize = landscape(A3)
    else:
        pagesize = landscape(A4)

    margin = 8 * mm
    doc = BaseDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=(schedule.name if schedule else "Thời khoá biểu"),
        author=tenant.name,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    ten, phu = _title_text(schedule, tenant)
    story = [
        Paragraph(_esc((tenant.name or "").upper()), st["subtitle"]),
        Paragraph(_esc(ten), st["title"]),
    ]
    if phu:
        story.append(Paragraph(_esc(phu), st["subtitle"]))
    story.append(Spacer(1, 4 * mm))

    if not groups:
        story.append(
            Paragraph(
                "Lịch chưa có buổi nào được xếp tiết.", st["subtitle"]
            )
        )
        doc.build(story)
        return buffer.getvalue()

    rows, spans, extra, col_ids = build_table(
        grid, groups, days, periods, morning_count, st
    )

    axis_w = [13 * mm, 10 * mm, 8 * mm]
    rest = doc.width - sum(axis_w)
    col_w = axis_w + [rest / len(col_ids)] * len(col_ids)

    table = Table(rows, colWidths=col_w, repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_GRID_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.9, COLOR_GRID),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, COLOR_GRID),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("BACKGROUND", (0, 1), (2, -1), COLOR_SHIFT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (2, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    style.extend(spans)
    style.extend(extra)
    table.setStyle(TableStyle(style))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
