from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param


def apply(ctx: BuildContext, rule):
    rcode = param(rule, "entity_code", "resource_code", "entity", default=None)
    for s in ctx.sessions:
        group_size = int(s.get("group_size", 0) or 0)
        for r in ctx.resources:
            if rcode and r["code"] != rcode:
                continue
            if int(r.get("capacity", 0)) >= group_size:
                continue
            for t in ctx.valid_starts.get(s["id"], []):
                x = ctx.X.get((s["id"], t, r["code"]))
                if x is not None:
                    ctx.model.Add(x == 0)
    return None
