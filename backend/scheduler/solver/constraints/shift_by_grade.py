from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    """Buổi văn hoá nằm đúng ca của khối; buổi nghề nằm ở ca bù.

    Trường cố định ca theo khối: khối 10 học văn hoá buổi sáng, khối 11
    buổi chiều, khối 12 cả ngày. Ca học nghề là phần còn lại của ngày, nên
    không cần khai riêng — suy ra được từ ca văn hoá.

    Không có ràng buộc này, bộ giải sẽ xếp tiết văn hoá khối 11 vào buổi
    sáng, sai hoàn toàn thực tế vận hành.
    """
    shifts = ctx.shift_by_session()
    if not shifts:
        return None

    morning = set(ctx.morning_indices())
    afternoon = set(range(ctx.num_timeslots)) - morning

    blocked = 0
    for sid, allowed in shifts.items():
        if allowed == "any":
            continue
        forbidden = afternoon if allowed == "morning" else morning
        for t in ctx.valid_starts.get(sid, []):
            dur = int(ctx.sessions_by_id[sid]["duration_slots"])
            run = ctx.covers(t, dur)
            # Cấm mọi vị trí bắt đầu khiến buổi rơi vào ca không được phép
            if run is None or any(p in forbidden for p in run):
                lit = ctx.start_lit.get((sid, t))
                if lit is not None:
                    ctx.model.Add(lit == 0)
                    blocked += 1
    if blocked:
        ctx.warnings.append(
            "shift_by_grade: chặn %d vị trí bắt đầu sai ca" % blocked
        )
    return None
