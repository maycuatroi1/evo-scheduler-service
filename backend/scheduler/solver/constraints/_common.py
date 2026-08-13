def param(rule, *keys, default=None):
    p = rule.get("params_json") or {}
    for k in keys:
        if k in p:
            return p[k]
    s = rule.get("scope_json") or {}
    for k in keys:
        if k in s:
            return s[k]
    return default


def affected_sessions(ctx, rule):
    etype = param(rule, "entity_type", "scope_type", default="teacher")
    if etype == "session":
        codes = param(rule, "entity_codes", "session_codes", "entity_code", "session_code", default=[])
        if isinstance(codes, str):
            codes = [codes]
        return [s for s in ctx.sessions if s["code"] in codes]
    if etype == "student_group":
        code = param(rule, "entity_code", "group_code", "entity", default=None)
        codes = param(rule, "entity_codes", "group_codes", default=None)
        if code and not codes:
            codes = [code]
        return [s for s in ctx.sessions if s.get("group_code") in (codes or [])]
    code = param(rule, "entity_code", "teacher_code", "entity", default=None)
    codes = param(rule, "entity_codes", "teacher_codes", default=None)
    if code and not codes:
        codes = [code]
    out = []
    for tc in codes or []:
        out.extend(ctx.sessions_by_teacher.get(tc, []))
    return out
