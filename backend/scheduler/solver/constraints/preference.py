from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param, affected_sessions


def _preferred_indices(ctx: BuildContext, rule):
    explicit = param(rule, "timeslots", "timeslot_indices", default=None)
    if explicit:
        return set(int(x) for x in explicit)
    target = param(rule, "target", "value", default=None)
    if target:
        t = str(target).lower()
        if t == "morning":
            return set(ctx.morning_indices())
        if t == "afternoon":
            return set(i for i in range(ctx.num_timeslots) if i not in ctx.morning_indices())
        return set(ctx.timeslots_for_day(target))
    day = param(rule, "day", "day_name", default=None)
    if day is not None:
        return set(ctx.timeslots_for_day(day))
    periods = param(rule, "periods", "period_indices", default=None)
    if periods is not None:
        return set(ctx.timeslots_for_period_in([int(x) for x in periods]))
    return set()


def apply(ctx: BuildContext, rule):
    preferred = _preferred_indices(ctx, rule)
    if not preferred:
        return None
    sessions = affected_sessions(ctx, rule)
    if not sessions:
        return None
    weight = int(rule.get("weight", 1) or 1)
    violation_vars = []
    for s in sessions:
        sid = s["id"]
        dur = int(s["duration_slots"])
        preferred_sum_terms = []
        for t in ctx.valid_starts.get(sid, []):
            run = ctx.covers(t, dur)
            if all(p in preferred for p in run):
                lit = ctx.start_lit.get((sid, t))
                if lit is not None:
                    preferred_sum_terms.append(lit)
        pref_sum = sum(preferred_sum_terms) if preferred_sum_terms else 0
        v = ctx.model.NewBoolVar(f"pref_viol_{sid}")
        ctx.model.Add(v + pref_sum == 1)
        violation_vars.append(v)
    total = ctx.model.NewIntVar(0, len(sessions), "pref_total")
    ctx.model.Add(total == sum(violation_vars))
    ctx.record_soft(rule, total, f"preference target={param(rule,'target','value',default='?')}")
    return weight * total
