from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    """Một giáo viên không dạy hai buổi cùng lúc.

    Buổi đã gán cứng giáo viên dùng khoảng thời gian bắt buộc; buổi để bộ giải
    tự chọn dùng khoảng tuỳ chọn gắn với biến chọn giáo viên.
    """
    by_teacher = {}
    for (sid, tc), interval in ctx.teacher_interval.items():
        by_teacher.setdefault(tc, []).append(interval)
    for tc, intervals in by_teacher.items():
        if len(intervals) >= 2:
            ctx.model.AddNoOverlap(intervals)
    return None
