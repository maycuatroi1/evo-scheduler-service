from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param, affected_sessions


def apply(ctx: BuildContext, rule):
    sessions = affected_sessions(ctx, rule)
    n = len(sessions)
    if n < 2:
        return None
    periods = [ctx.start_period[s["id"]] for s in sessions]
    days = [ctx.start_day[s["id"]] for s in sessions]
    ctx.model.AddAllDifferent(periods)
    ref_day = days[0]
    for d in days[1:]:
        ctx.model.Add(d == ref_day)
    min_p = ctx.model.NewIntVar(0, ctx.num_timeslots, "adj_min")
    max_p = ctx.model.NewIntVar(0, ctx.num_timeslots, "adj_max")
    ctx.model.AddMinEquality(min_p, periods)
    ctx.model.AddMaxEquality(max_p, periods)
    ctx.model.Add(max_p - min_p == n - 1)
    return None
