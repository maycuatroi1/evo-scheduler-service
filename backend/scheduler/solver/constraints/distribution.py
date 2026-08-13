from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param


def apply(ctx: BuildContext, rule):
    etype = param(rule, "entity_type", "scope_type", default="teacher")
    if etype != "teacher":
        return None
    codes = param(rule, "entity_codes", "teacher_codes", default=None)
    if not codes:
        codes = [t["code"] for t in ctx.teachers if ctx.sessions_by_teacher.get(t["code"])]
    loads = []
    for tc in codes:
        sessions = ctx.sessions_by_teacher.get(tc, [])
        if not sessions:
            continue
        terms = []
        for s in sessions:
            for p in range(ctx.num_timeslots):
                occ = ctx.occ.get((s["id"], p))
                if occ is not None:
                    terms.append(occ)
        if terms:
            load = ctx.model.NewIntVar(0, ctx.num_timeslots * len(sessions), f"dist_load_{tc}")
            ctx.model.Add(load == sum(terms))
            loads.append(load)
    if len(loads) < 2:
        return None
    weight = int(rule.get("weight", 1) or 1)
    hi = ctx.model.NewIntVar(0, ctx.num_timeslots * max(len(ctx.sessions_by_teacher.get(c, [])) for c in codes), "dist_max")
    lo = ctx.model.NewIntVar(0, ctx.num_timeslots, "dist_min")
    ctx.model.AddMaxEquality(hi, loads)
    ctx.model.AddMinEquality(lo, loads)
    spread = ctx.model.NewIntVar(0, ctx.num_timeslots, "dist_spread")
    ctx.model.Add(spread == hi - lo)
    ctx.record_soft(rule, spread, "distribution teacher load spread")
    return weight * spread
