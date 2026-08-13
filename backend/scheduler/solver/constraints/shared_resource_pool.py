from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    for r in ctx.resources:
        rcode = r["code"]
        cap = int(r.get("available_quantity", 1) or 1)
        for p in range(ctx.num_timeslots):
            terms = []
            for s in ctx.sessions:
                sid = s["id"]
                for t in ctx.valid_starts.get(sid, []):
                    if p in ctx.covers(t, s["duration_slots"]):
                        x = ctx.X.get((sid, t, rcode))
                        if x is not None:
                            terms.append(x)
            if terms:
                ctx.model.Add(sum(terms) <= cap)
    return None
