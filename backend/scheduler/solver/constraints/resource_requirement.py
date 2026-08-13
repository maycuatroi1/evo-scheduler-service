from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param

DEFAULT_COMPAT = {
    "theory": ["theory_room"],
    "practice": ["workshop", "tool_set"],
}


def _allowed_types(rule, session_type):
    compat = param(rule, "compat", "compatibility", default=None)
    if compat and session_type in compat:
        allowed = compat[session_type]
        return allowed if isinstance(allowed, list) else [allowed]
    explicit = param(rule, "allowed_types", "allowed_resource_types", default=None)
    if explicit:
        return explicit if isinstance(explicit, list) else [explicit]
    target_type = param(rule, "session_type", default=None)
    allowed = param(rule, "allowed_resource_type", default=None)
    if target_type and session_type == target_type and allowed:
        return [allowed] if isinstance(allowed, str) else allowed
    return DEFAULT_COMPAT.get(session_type, [])


def apply(ctx: BuildContext, rule):
    for s in ctx.sessions:
        allowed = _allowed_types(rule, s["session_type"])
        allowed_lower = {a.lower() for a in allowed}
        for r in ctx.resources:
            if r["type"].lower() in allowed_lower:
                continue
            for t in ctx.valid_starts.get(s["id"], []):
                x = ctx.X.get((s["id"], t, r["code"]))
                if x is not None:
                    ctx.model.Add(x == 0)
    return None
