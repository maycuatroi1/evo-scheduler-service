from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param

#: Trần sĩ số theo loại buổi, theo TT 07/2017/TT-BLĐTBXH.
DEFAULT_CAPS = {"theory": 35, "practice": 18, "practice_hazardous": 10}


def apply(ctx: BuildContext, rule):
    """Trần sĩ số theo loại buổi, tách khỏi sức chứa vật lý của phòng.

    Đây là ràng buộc pháp lý, không phải ràng buộc vật lý: một xưởng 30
    chỗ vẫn không được nhận nhóm thực hành 30 người, vì quy định giới hạn
    lớp thực hành ở 18 học viên (10 với nghề nặng nhọc, độc hại).

    Ràng buộc này chính là lý do trường phải tách lớp văn hoá thành nhiều
    nhóm nghề. Nếu nhóm vượt trần, đây là lỗi dữ liệu chứ không phải lỗi
    xếp lịch — bộ giải không tự tách nhóm được, nên chỉ ghi cảnh báo để
    tiền kiểm tra báo cho người dùng.
    """
    caps = dict(DEFAULT_CAPS)
    override = param(rule, "caps", "limits", default=None)
    if isinstance(override, dict):
        for k, v in override.items():
            try:
                caps[k] = int(v)
            except (TypeError, ValueError):
                continue

    over = []
    for s in ctx.sessions:
        size = int(s.get("group_size", 0) or 0)
        if size <= 0:
            continue
        stype = s.get("session_type")
        if stype == "practice":
            key = "practice_hazardous" if s.get("hazardous") else "practice"
        elif stype == "theory":
            key = "theory"
        else:
            continue  # thực tập, bổ trợ không áp trần
        cap = caps.get(key)
        if cap and size > cap:
            over.append((s.get("code") or s["id"], size, cap))

    if over:
        for code, size, cap in over[:10]:
            ctx.warnings.append(
                "capacity_by_type: %s có %d học viên, vượt trần %d — cần tách nhóm"
                % (code, size, cap)
            )
        if len(over) > 10:
            ctx.warnings.append(
                "capacity_by_type: còn %d nhóm khác vượt trần" % (len(over) - 10)
            )
    return None
