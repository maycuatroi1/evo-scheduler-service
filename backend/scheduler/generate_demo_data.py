"""
Generate a large realistic + FEASIBLE weekly Excel for evo-scheduler-service demo.

Feasibility budget (weekly horizon = 6 days x 5 periods = 30 slots):
- Culture tier: 25 classes x 10 sessions/week (avg 2.4 slots) ~ 600 room-slots
  vs 30 theory rooms x 30 slots = 900 capacity (67% util) - OK
  Class load: ~24/30 slots (80%) - OK
  Teachers: 250 sessions, 40 culture teachers (~6.3 sessions each) - OK
- Vocational tier: 30 classes x 3 sessions/week (2 practice in workshop
  + 1 theory in room). Practice demand 60 x 3.5 = 210 workshop-slots
  vs 14 workshops x 30 = 420 (50% util) - OK
- Students ~1450.
"""
import random
import sys

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

random.seed(2026)

LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý",
]
MALE_NAMES = [
    "Văn An", "Văn Bình", "Văn Cường", "Văn Đức", "Văn Đông", "Văn Hà",
    "Văn Hùng", "Văn Khánh", "Văn Long", "Văn Minh", "Văn Nam", "Văn Phong",
    "Văn Quân", "Văn Sơn", "Văn Thành", "Văn Trung", "Hoàng Nam", "Hoàng Long",
    "Đức Anh", "Minh Tuấn", "Quang Huy", "Thanh Hải", "Công Minh",
    "Tiến Dũng", "Bảo Khánh", "Trọng Nhân",
]
FEMALE_NAMES = [
    "Thị Bình", "Thị Châu", "Thị Dung", "Thị Hà", "Thị Hằng", "Thị Hồng",
    "Thị Lan", "Thị Liễu", "Thị Mai", "Thị Ngọc", "Thị Phương", "Thị Quỳnh",
    "Thị Sen", "Thị Thanh", "Thị Thu", "Thị Trâm", "Thị Vân", "Thị Xuân",
    "Thị Yến", "Thị Hoa", "Thị Hương", "Thị Loan", "Thị Mỹ", "Thị Nga",
    "Thị Oanh", "Thị Uyên",
]
DEPARTMENTS = ["Điện", "Cơ khí", "Xây dựng", "Điện tử", "Công nghệ ô tô"]

CULTURE_SUBJECTS = [
    ("MH_TOAN", "Toán học", 2),
    ("MH_VAN", "Ngữ văn", 2),
    ("MH_LY", "Vật lý", 1),
    ("MH_ANH", "Tiếng Anh", 1),
    ("MH_SU", "Lịch sử", 1),
]

CULTURE_TEACHERS_PER_SUBJECT = {
    "MH_TOAN": 12,
    "MH_VAN": 12,
    "MH_LY": 6,
    "MH_ANH": 6,
    "MH_SU": 6,
}

VOC_MODULES_BY_DEPT = {
    "Điện": [
        ("ĐIỆN1", "Kỹ thuật điện cơ bản"),
        ("ĐIỆN2", "Lắp đặt điện công nghiệp"),
        ("VDK", "Lập trình vi điều khiển"),
        ("ATLD", "An toàn lao động"),
    ],
    "Cơ khí": [
        ("CƠKHÍ", "Kỹ thuật cơ khí"),
        ("HÀN", "Kỹ thuật hàn"),
        ("CAD", "CAD/CAM cơ khí"),
        ("ATLD2", "An toàn lao động"),
    ],
    "Xây dựng": [
        ("XD1", "Kỹ thuật xây dựng"),
        ("THỢXÂY", "Thợ xây cơ bản"),
        ("VẬTLIỆU", "Thí nghiệm vật liệu"),
    ],
    "Điện tử": [
        ("ĐT1", "Kỹ thuật điện tử"),
        ("ĐT2", "Đo lường điện tử"),
        ("ATLD3", "An toàn lao động"),
    ],
    "Công nghệ ô tô": [
        ("ÔTÔ1", "Kỹ thuật sửa chữa ô tô"),
        ("ÔTÔ2", "Động cơ ô tô"),
        ("ATLD4", "An toàn lao động"),
    ],
}

WORKSHOPS_BY_DEPT = {
    "Điện": [
        ("XN_DIEN1", "Xưởng điện công nghiệp 1", 20),
        ("XN_DIEN2", "Xưởng điện công nghiệp 2", 15),
        ("XN_VDK", "Xưởng vi điều khiển", 12),
    ],
    "Cơ khí": [
        ("XN_COKHI1", "Xưởng cơ khí 1", 20),
        ("XN_COKHI2", "Xưởng hàn - gò", 15),
    ],
    "Xây dựng": [
        ("XN_XD1", "Xưởng thí nghiệm vật liệu", 20),
        ("XN_XD2", "Xưởng thực hành thợ xây", 15),
    ],
    "Điện tử": [
        ("XN_DT1", "Xưởng điện tử 1", 20),
        ("XN_DT2", "Xưởng điện tử 2", 12),
    ],
    "Công nghệ ô tô": [
        ("XN_OTO1", "Xưởng sửa chữa ô tô", 10),
        ("XN_OTO2", "Xưởng động cơ", 8),
    ],
}

TOOL_SETS = [
    ("TS_DIEN_01", "Bộ dụng cụ điện A", 5),
    ("TS_DIEN_02", "Bộ dụng cụ điện B", 5),
    ("TS_DIEN_03", "Bộ đo điện đa năng", 8),
    ("TS_COKHI_01", "Bộ dụng cụ cơ khí A", 6),
    ("TS_COKHI_02", "Bộ dụng cụ cơ khí B", 6),
    ("TS_HAN_01", "Bộ dụng cụ hàn", 4),
    ("TS_XD_01", "Bộ dụng cụ xây dựng A", 8),
    ("TS_XD_02", "Bộ dụng cụ xây dựng B", 8),
    ("TS_OTO_01", "Bộ dụng cụ ô tô", 5),
    ("TS_VDK_01", "Board Arduino + linh kiện", 10),
    ("TS_VDK_02", "Board mô phỏng PLC", 6),
    ("TS_DT_01", "Bộ dụng cụ điện tử A", 8),
    ("TS_DT_02", "Máy hiện sóng", 4),
    ("TS_VTL_01", "Bộ thí nghiệm vật liệu", 6),
]

HEADER_FILL = PatternFill(start_color="FF1F4E78", end_color="FF1F4E78", fill_type="solid")
HEADER_FONT = Font(color="FFFFFFFF", bold=True)
HEADER_ALIGN = Alignment(horizontal="center", vertical="center")

NUM_CULTURE_TEACHERS_PER_SUBJECT = 5
NUM_CULTURE_TEACHERS_OVERRIDES = CULTURE_TEACHERS_PER_SUBJECT
NUM_VOC_TEACHERS_PER_DEPT = 8
NUM_THEORY_ROOMS = 30
NUM_CULTURE_CLASSES = 15
NUM_DUAL_CLASSES = 10
NUM_VOC_CLASSES_PER_DEPT = 6


def make_name():
    ln = random.choice(LAST_NAMES)
    fn = random.choice(MALE_NAMES if random.random() < 0.5 else FEMALE_NAMES)
    return f"{ln} {fn}"


def build_data():
    teachers = []          # (code, name, block_label, quota)
    student_groups = []    # (code, name, enrollment, size)
    resources = []         # (code, name, type_label, capacity, qty, avail)
    modules = []           # (code, name, theory_h, practice_h, group_code)
    teacher_modules = []   # (teacher_code, module_code)
    sessions = []          # (module_code, group_code, type_label, slots, tier_label, resource, teachers)

    gv = 0

    culture_teachers = {}
    for mcode, mname, _ in CULTURE_SUBJECTS:
        pool = []
        n = CULTURE_TEACHERS_PER_SUBJECT.get(mcode, NUM_CULTURE_TEACHERS_PER_SUBJECT)
        for _ in range(n):
            gv += 1
            code = f"GV{gv:03d}"
            teachers.append((code, make_name(), "Văn hóa", random.choice([16, 18, 20])))
            pool.append(code)
        culture_teachers[mcode] = pool

    voc_teachers = {}
    for dept in DEPARTMENTS:
        pool = []
        for _ in range(NUM_VOC_TEACHERS_PER_DEPT):
            gv += 1
            code = f"GV{gv:03d}"
            teachers.append((code, make_name(), "Nghề", random.choice([14, 16, 18])))
            pool.append(code)
        voc_teachers[dept] = pool

    for i in range(NUM_THEORY_ROOMS):
        code = f"P{i + 1:03d}"
        cap = random.choice([40, 45, 50])
        resources.append((code, f"Phòng lý thuyết {i + 1:03d}", "Phòng lý thuyết", cap, 1, 1))
    theory_rooms = [r[0] for r in resources]

    for dept, ws_list in WORKSHOPS_BY_DEPT.items():
        for code, name, cap in ws_list:
            resources.append((code, name, "Xưởng", cap, 1, 1))
    workshop_by_dept = {
        dept: [c for c, _, _ in ws]
        for dept, ws in WORKSHOPS_BY_DEPT.items()
    }

    for code, name, qty in TOOL_SETS:
        resources.append((code, name, "Bộ dụng cụ", 0, qty, qty))

    culture_classes = []
    for i in range(NUM_CULTURE_CLASSES):
        code = f"VH{i + 1:02d}"
        student_groups.append((code, f"Lớp Văn hóa {i + 1:02d}", "Cao đẳng", random.randint(38, 48)))
        culture_classes.append(code)
    for i in range(NUM_DUAL_CLASSES):
        code = f"SB{i + 1:02d}"
        student_groups.append((code, f"Lớp Song bằng {i + 1:02d}", "Song bằng", random.randint(35, 42)))
        culture_classes.append(code)

    voc_classes = []
    for dept in DEPARTMENTS:
        for i in range(NUM_VOC_CLASSES_PER_DEPT):
            idx = len(voc_classes) + 1
            code = f"NG{idx:02d}"
            size = random.choice([12, 15, 18, 20])
            student_groups.append((code, f"Lớp Nghề {dept} {i + 1}", "Cao đẳng", size))
            voc_classes.append((code, dept, size))

    total_students = sum(r[3] for r in student_groups)

    for cls in culture_classes:
        for mcode, mname, weekly in CULTURE_SUBJECTS:
            full = f"{mcode}_{cls}"
            theory_h = weekly * 30
            modules.append((full, f"{mname} - {cls}", theory_h, 0, cls))
            pool = culture_teachers[mcode]
            for tcode in random.sample(pool, k=min(2, len(pool))):
                teacher_modules.append((tcode, full))
            for _ in range(weekly):
                room = random.choice(theory_rooms)
                tc = random.choice(pool)
                sessions.append((full, cls, "Lý thuyết", random.choice([2, 3]), "Văn hóa", room, tc))

    for code, dept, size in voc_classes:
        dept_modules = VOC_MODULES_BY_DEPT[dept]
        chosen = random.sample(dept_modules, k=2)
        for mcode, mname in chosen:
            full = f"{mcode}_{code}"
            modules.append((full, f"{mname} - {code}", 15, 60, code))
            pool = voc_teachers[dept]
            for tcode in random.sample(pool, k=min(3, len(pool))):
                teacher_modules.append((tcode, full))
            room = random.choice(theory_rooms)
            tc = random.choice(pool)
            sessions.append((full, code, "Lý thuyết", 2, "Nghề", room, tc))
            ws = random.choice(workshop_by_dept[dept])
            tc2 = random.choice(pool)
            sessions.append((full, code, "Thực hành", random.choice([3, 4]), "Nghề", ws, tc2))

    return teachers, student_groups, resources, modules, teacher_modules, sessions, total_students


def write_sheet(ws, headers, rows):
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
    for row_idx, row_data in enumerate(rows, start=2):
        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 24


def generate(filepath):
    teachers, groups, resources, modules, tm, sessions, total_students = build_data()

    culture_sessions = [s for s in sessions if s[4] == "Văn hóa"]
    voc_sessions = [s for s in sessions if s[4] == "Nghề"]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    write_sheet(wb.create_sheet("Giáo viên"), ["Mã GV", "Họ tên", "Khối", "Định mức"], teachers)
    write_sheet(wb.create_sheet("Lớp học"), ["Mã LH", "Tên LH", "Loại hình", "Sĩ số"], groups)
    write_sheet(wb.create_sheet("Thiết bị"),
                ["Mã TB", "Tên TB", "Loại", "Sức chứa", "Số lượng", "Còn lại"], resources)
    write_sheet(wb.create_sheet("Môn học"),
                ["Mã MH", "Tên MH", "Lý thuyết", "Thực hành", "Mã LH"], modules)
    write_sheet(wb.create_sheet("GV - Môn học"), ["Mã GV", "Mã MH"], tm)
    write_sheet(wb.create_sheet("Tiết cố định"),
                ["Mã MH", "Mã LH", "Loại", "Số tiết", "Cấp", "Mã TB", "Mã GV"], sessions)

    wb.save(filepath)

    culture_slot_demand = sum(s[3] for s in culture_sessions)
    voc_practice_demand = sum(s[3] for s in voc_sessions if s[2] == "Thực hành")
    return {
        "teachers": len(teachers),
        "student_groups": len(groups),
        "total_students": total_students,
        "theory_rooms": NUM_THEORY_ROOMS,
        "workshops": sum(len(v) for v in WORKSHOPS_BY_DEPT.values()),
        "tool_sets": len(TOOL_SETS),
        "modules": len(modules),
        "teacher_modules": len(tm),
        "sessions": len(sessions),
        "culture_sessions": len(culture_sessions),
        "vocational_sessions": len(voc_sessions),
        "culture_room_slot_demand": culture_slot_demand,
        "culture_room_capacity": NUM_THEORY_ROOMS * 30,
        "voc_workshop_slot_demand": voc_practice_demand,
        "voc_workshop_capacity": sum(len(v) for v in WORKSHOPS_BY_DEPT.values()) * 30,
    }


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_large.xlsx"
    stats = generate(out)
    print(f"Generated: {out}")
    for k, v in stats.items():
        print(f"  {k}: {v}")
