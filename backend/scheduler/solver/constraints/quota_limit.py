from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param

SCALE = 100


def apply(ctx: BuildContext, rule):
    teacher_code = param(rule, "entity_code", "teacher_code", "entity", default=None)
    teacher_codes = param(rule, "entity_codes", "teacher_codes", default=None)
    if teacher_code and not teacher_codes:
        teacher_codes = [teacher_code]
    if not teacher_codes:
        teacher_codes = [t["code"] for t in ctx.teachers]
    hours_per_slot = float(ctx.hours_per_slot or 1.0)
    per_slot_decis = int(round(hours_per_slot * SCALE))
    if per_slot_decis <= 0:
        per_slot_decis = SCALE
    quota_map = {t["code"]: t.get("quota_standard_hours") for t in ctx.teachers}
    for tc in teacher_codes:
        quota = quota_map.get(tc)
        if not quota:
            continue
        quota_decis = int(round(float(quota) * SCALE))
        sessions = ctx.sessions_by_teacher.get(tc, [])
        if not sessions:
            continue
        total = []
        for s in sessions:
            slot_weight = int(s["duration_slots"]) * per_slot_decis
            chosen = []
            for t in ctx.valid_starts.get(s["id"], []):
                for rcode in ctx.candidate_resources.get(s["id"], []):
                    x = ctx.X.get((s["id"], t, rcode))
                    if x is not None:
                        chosen.append(x)
            if chosen:
                total.append((slot_weight, chosen))
        if not total:
            continue
        terms = []
        for slot_weight, chosen in total:
            terms.append(slot_weight * sum(chosen))
        ctx.model.Add(sum(terms) <= quota_decis)
    return None
