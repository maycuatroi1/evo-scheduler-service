from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    """Một lớp không học hai buổi cùng lúc."""
    for grp, sessions in ctx.sessions_by_group.items():
        intervals = [
            ctx.interval[s["id"]] for s in sessions if s["id"] in ctx.interval
        ]
        if len(intervals) >= 2:
            ctx.model.AddNoOverlap(intervals)
    return None
