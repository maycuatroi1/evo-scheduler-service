from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param, affected_sessions


def _blocked_indices(ctx: BuildContext, rule):
    explicit = param(rule, "timeslots", "timeslot_indices", default=None)
    if explicit:
        return [int(x) for x in explicit]
    day = param(rule, "day", "day_name", default=None)
    if day is not None:
        return ctx.timeslots_for_day(day)
    periods = param(rule, "periods", "period_indices", default=None)
    if periods is not None:
        return ctx.timeslots_for_period_in([int(x) for x in periods])
    if param(rule, "morning", default=None):
        return ctx.morning_indices()
    if param(rule, "afternoon", default=None):
        return [i for i in range(ctx.num_timeslots) if i not in ctx.morning_indices()]
    return []


def apply(ctx: BuildContext, rule):
    etype = param(rule, "entity_type", "scope_type", default="teacher")
    blocked = set(_blocked_indices(ctx, rule))
    if not blocked:
        return None
    if etype == "resource":
        rcode = param(rule, "entity_code", "resource_code", "entity", default=None)
        for s in ctx.sessions:
            sid = s["id"]
            res_lit = ctx.assign.get((sid, rcode))
            if res_lit is None:
                continue
            duration = int(s["duration_slots"])
            for t in ctx.valid_starts.get(sid, []):
                if not any(p in blocked for p in ctx.covers(t, duration)):
                    continue
                start_lit = ctx.start_lit.get((sid, t))
                if start_lit is not None:
                    # Không được vừa bắt đầu ở tiết này vừa dùng tài nguyên đó.
                    ctx.model.AddBoolOr([start_lit.Not(), res_lit.Not()])
        return None
    for s in affected_sessions(ctx, rule):
        for p in blocked:
            occ = ctx.occ.get((s["id"], p))
            if occ is not None:
                ctx.model.Add(occ == 0)
    return None
