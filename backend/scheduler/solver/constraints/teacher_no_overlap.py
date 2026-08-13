from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    teacher_fixed = {}
    teacher_variable = {}
    for s in ctx.sessions:
        sid = s["id"]
        for tc in s.get("teacher_codes", []):
            teacher_fixed.setdefault(tc, []).append(sid)
        for tc in ctx.eligible_teachers.get(sid, []):
            teacher_variable.setdefault(tc, []).append(sid)

    all_teachers = set(teacher_fixed) | set(teacher_variable)
    for tc in all_teachers:
        fixed = teacher_fixed.get(tc, [])
        variable = teacher_variable.get(tc, [])
        if len(fixed) + len(variable) < 2:
            continue
        for p in range(ctx.num_timeslots):
            terms = []
            for sid in fixed:
                occ = ctx.occ.get((sid, p))
                if occ is not None:
                    terms.append(occ)
            for sid in variable:
                y = ctx.Y.get((sid, tc))
                occ = ctx.occ.get((sid, p))
                if y is not None and occ is not None:
                    z = ctx.model.NewBoolVar(f"zt_{sid}_{tc}_{p}")
                    ctx.model.Add(z <= y)
                    ctx.model.Add(z <= occ)
                    ctx.model.Add(z >= y + occ - 1)
                    terms.append(z)
            if len(terms) >= 2:
                ctx.model.Add(sum(terms) <= 1)
    return None
