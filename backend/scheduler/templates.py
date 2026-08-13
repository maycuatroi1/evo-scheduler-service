import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from scheduler.excel_parser import SHEET_NAMES

SHEET_HEADERS = {
    "Teachers": ["Ma GV", "Ho ten", "Blocks", "Quota"],
    "StudentGroups": ["Ma LH", "Ten LH", "Loai hinh", "Si so"],
    "Resources": ["Ma TB", "Ten TB", "Loai", "Suc chua", "So luong", "Con lai"],
    "Modules": ["Ma MH", "Ten MH", "LT", "TH", "Ma LH"],
    "TeacherModule": ["Ma GV", "Ma MH"],
    "FixedSessions": ["Ma MH", "Ma LH", "Loai", "So tiet", "Cap", "Ma TB", "Ma GV"],
}

EXAMPLE_ROWS = {
    "Teachers": [
        ["GV001", "Nguyen Van A", "culture", 14],
        ["GV002", "Tran Thi B", "vocational", 16],
    ],
    "StudentGroups": [
        ["LH001", "Lop 10A1", "dual_degree", 30],
        ["LH002", "Lop 11B2", "college", 25],
    ],
    "Resources": [
        ["P101", "Phong Ly thuyet 101", "theory_room", 40, 1, 1],
        ["TS01", "Bo dung cu thuc hanh", "tool_set", 0, 10, 10],
    ],
    "Modules": [
        ["MH001", "Toan hoc", 60, 0, "LH001"],
        ["MH002", "Co khi", 0, 90, "LH002"],
    ],
    "TeacherModule": [
        ["GV001", "MH001"],
        ["GV002", "MH002"],
    ],
    "FixedSessions": [
        ["MH001", "LH001", "theory", 3, "culture", "P101", "GV001"],
        ["MH002", "LH002", "practice", 4, "vocational", "TS01", "GV002"],
    ],
}

HEADER_FILL = PatternFill(start_color="FF1F4E78", end_color="FF1F4E78", fill_type="solid")
HEADER_FONT = Font(color="FFFFFFFF", bold=True)
HEADER_ALIGN = Alignment(horizontal="center", vertical="center")


def _write_sheet(wb, sheet_name, headers, examples):
    ws = wb.create_sheet(title=sheet_name)
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
    for row_idx, row_data in enumerate(examples, start=2):
        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    for col_idx in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_idx)
        max_len = len(str(headers[col_idx - 1]))
        for row_data in examples:
            if col_idx - 1 < len(row_data):
                max_len = max(max_len, len(str(row_data[col_idx - 1])))
        ws.column_dimensions[column_letter].width = min(max_len + 4, 40)


def generate_template():
    wb = Workbook()
    wb.remove(wb.active)
    for sheet_name in SHEET_NAMES:
        _write_sheet(
            wb,
            sheet_name,
            SHEET_HEADERS[sheet_name],
            EXAMPLE_ROWS[sheet_name],
        )
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
