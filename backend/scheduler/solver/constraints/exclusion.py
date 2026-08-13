from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param, affected_sessions


def apply(ctx: BuildContext, rule):
    etype = param(rule, "entity_type", "scope_type", default="teacher")
    if etype == "pair":
        return _apply_pair(ctx, rule)
    sessions = affected_sessions(ctx, rule)
    if len(sessions) < 2:
        return None
    for p in range(ctx.num_timeslots):
        terms = []
        for s in sessions:
            occ = ctx.occ.get((s["id"], p))
            if occ is not None:
                terms.append(occ)
        if terms:
            ctx.model.Add(sum(terms) <= 1)
    return None


def _apply_pair(ctx: BuildContext, rule):
    left = param(rule, "left", "a", default=None)
    right = param(rule, "right", "b", default=None)
    pairs = param(rule, "pairs", default=None)
    pair_list = []
    if pairs:
        for pr in pairs:
            pair_list.append((pr[0], pr[1]))
    if left and right:
        pair_list.append((left, right))
    for a, b in pair_list:
        sa = next((s for s in ctx.sessions if s["code"] == a), None)
        sb = next((s for s in ctx.sessions if s["code"] == b), None)
        if not sa or not sb:
            continue
        for p in range(ctx.num_timeslots):
            oa = ctx.occ.get((sa["id"], p))
            ob = ctx.occ.get((sb["id"], p))
            if oa is not None and ob is not None:
                ctx.model.Add(oa + ob <= 1)
    return None
