from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    for tc, sessions in ctx.sessions_by_teacher.items():
        if len(sessions) < 2:
            continue
        sids = [s["id"] for s in sessions]
        for p in range(ctx.num_timeslots):
            terms = [ctx.occ[(sid, p)] for sid in sids if (sid, p) in ctx.occ]
            if len(terms) >= 2:
                ctx.model.Add(sum(terms) <= 1)
    return None
