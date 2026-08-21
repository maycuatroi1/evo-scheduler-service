from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    """Các nhóm nghề cùng một lớp văn hoá không được học trùng giờ.

    Học sinh hệ 9+ sinh hoạt theo lớp văn hoá nhưng học nghề theo nhóm
    nghề, và một lớp có thể tách thành nhiều nhóm (11A3 tách ba nhóm
    16/17/30 trong thời khoá biểu của trường). Cùng một em không thể vừa
    ngồi xưởng vừa ngồi lớp văn hoá, nên mọi buổi của các nhóm chung lớp
    gốc phải loại trừ nhau.

    Chiều ngược lại cũng đúng: một nhóm nghề gộp nhiều lớp (12A1 + 12A4)
    thì buổi của nhóm ấy chặn tất cả các lớp thành viên. Cả hai chiều đều
    quy về "các buổi chạm cùng một lớp văn hoá thì không chồng nhau".
    """
    homerooms = ctx.homerooms_by_session()
    if not homerooms:
        return None

    # Gom buổi học theo từng lớp văn hoá mà nó chạm tới
    by_home = {}
    for sid, codes in homerooms.items():
        for code in codes:
            by_home.setdefault(code, []).append(sid)

    for code, sids in by_home.items():
        intervals = [ctx.interval[sid] for sid in sids if sid in ctx.interval]
        if len(intervals) >= 2:
            ctx.model.AddNoOverlap(intervals)
    return None
