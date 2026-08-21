from scheduler.solver.context import BuildContext

#: Ràng buộc mềm: vi phạm vẫn ra được lịch, chỉ là lịch kém đẹp hơn.
DEFAULT_WEIGHT = 3


def apply(ctx: BuildContext, rule):
    """Ràng buộc cá nhân của từng giáo viên.

    Ba thứ khai trong hồ sơ giáo viên mà trước đây bộ giải không đọc tới,
    nên người dùng khai xong không thấy tác dụng gì:

    - **Tối đa tiết mỗi buổi** — tránh dồn 8 tiết vào một buổi.
    - **Tối thiểu tiết mỗi buổi** — tránh bắt giáo viên đến trường chỉ để
      dạy một tiết rồi về.
    - **Số ngày nghỉ trong tuần** — giáo viên cần ngày trống để soạn bài.

    Cả ba là ràng buộc mềm: nếu ép cứng, một trường đông lớp sẽ không có
    lời giải nào. Vi phạm bị phạt theo trọng số để bộ giải cố tránh.
    """
    weight = int(rule.get("weight", DEFAULT_WEIGHT) or DEFAULT_WEIGHT)
    terms = []
    days = sorted({ts["day"] for ts in ctx.horizon})

    for t in ctx.teachers:
        code = t.get("code")
        sessions = ctx.sessions_by_teacher.get(code, [])
        if not sessions:
            continue

        hi = t.get("max_periods_per_session")
        lo = t.get("min_periods_per_session")
        off = t.get("days_off_per_week")
        if hi is None and lo is None and off is None:
            continue

        # Số tiết dạy mỗi ngày, và cờ "có dạy ngày này không"
        loads, busy_flags = [], []
        for d in days:
            slots = [i for i, ts in enumerate(ctx.horizon) if ts["day"] == d]
            occ = []
            for s in sessions:
                for p in slots:
                    v = ctx.occ.get((s["id"], p))
                    if v is not None:
                        occ.append(v)
            if not occ:
                continue
            load = ctx.model.NewIntVar(0, len(slots), f"tl_{code}_{d}")
            ctx.model.Add(load == sum(occ))
            loads.append(load)

            busy = ctx.model.NewBoolVar(f"tb_{code}_{d}")
            ctx.model.Add(load >= 1).OnlyEnforceIf(busy)
            ctx.model.Add(load == 0).OnlyEnforceIf(busy.Not())
            busy_flags.append(busy)

            if hi:
                over = ctx.model.NewIntVar(0, len(slots), f"tover_{code}_{d}")
                ctx.model.Add(over >= load - int(hi))
                ctx.model.Add(over >= 0)
                terms.append(over)

            if lo:
                # Chỉ phạt khi có dạy: ngày nghỉ không tính là thiếu tiết
                under = ctx.model.NewIntVar(0, int(lo), f"tunder_{code}_{d}")
                ctx.model.Add(under >= int(lo) - load).OnlyEnforceIf(busy)
                ctx.model.Add(under == 0).OnlyEnforceIf(busy.Not())
                terms.append(under)

        if off and busy_flags:
            want_busy = max(0, len(days) - int(off))
            excess = ctx.model.NewIntVar(0, len(days), f"toff_{code}")
            ctx.model.Add(excess >= sum(busy_flags) - want_busy)
            ctx.model.Add(excess >= 0)
            terms.append(excess)

    if not terms:
        return None

    total = ctx.model.NewIntVar(0, 10_000, "teacher_limits_total")
    ctx.model.Add(total == sum(terms))
    ctx.record_soft(rule, total, "teacher personal limits")
    return weight * total
