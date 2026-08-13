from scheduler.solver.context import BuildContext


DEFAULT_WEIGHTS = {
    "idle_teacher": 3,
    "room_change": 2,
    "compact_schedule": 5,
    "teacher_load_balance": 4,
}

KNOWN_WEIGHT_KEYS = set(DEFAULT_WEIGHTS.keys())


def merge_weights(overrides):
    merged = dict(DEFAULT_WEIGHTS)
    if not overrides:
        return merged
    for k, v in overrides.items():
        if k not in KNOWN_WEIGHT_KEYS:
            continue
        try:
            merged[k] = int(v)
        except (TypeError, ValueError):
            continue
    return merged


def _default_rule(key, weight):
    return {
        "id": -1,
        "type": "default:" + key,
        "hardness": "soft",
        "weight": weight,
        "active": True,
    }


def _days(ctx):
    out = {}
    for g, ts in enumerate(ctx.horizon):
        out.setdefault(ts["day"], []).append(g)
    return out


def _max_periods_per_day(ctx):
    counts = {}
    for ts in ctx.horizon:
        counts[ts["day"]] = counts.get(ts["day"], 0) + 1
    return max(counts.values()) if counts else 1


def _max_period_index(ctx):
    return max((ts["period"] for ts in ctx.horizon), default=0)


def _idle_teacher(ctx):
    days = _days(ctx)
    model = ctx.model
    max_period = _max_period_index(ctx)
    penalties = []
    for tc, sessions in ctx.sessions_by_teacher.items():
        if not sessions:
            continue
        sids = [s["id"] for s in sessions]
        for d, globals_in_day in days.items():
            busy_pairs = []
            for g in globals_in_day:
                p_local = ctx.horizon[g]["period"]
                terms = [ctx.occ[(sid, g)] for sid in sids if (sid, g) in ctx.occ]
                if not terms:
                    continue
                b = model.NewBoolVar("idle_busy_%s_%s_%s" % (tc, d, p_local))
                model.AddMaxEquality(b, terms)
                busy_pairs.append((p_local, b))
            if not busy_pairs:
                continue
            busy_list = [b for _, b in busy_pairs]
            has_any = model.NewBoolVar("idle_any_%s_%s" % (tc, d))
            model.AddMaxEquality(has_any, busy_list)
            used = model.NewIntVar(0, len(busy_list), "idle_used_%s_%s" % (tc, d))
            model.Add(used == sum(busy_list))
            contribs_max = [p * b for p, b in busy_pairs]
            max_local = model.NewIntVar(0, max_period, "idle_maxp_%s_%s" % (tc, d))
            model.AddMaxEquality(max_local, contribs_max)
            inv_contribs = [(max_period - p) * b for p, b in busy_pairs]
            max_inv = model.NewIntVar(0, max_period, "idle_maxinv_%s_%s" % (tc, d))
            model.AddMaxEquality(max_inv, inv_contribs)
            min_local = model.NewIntVar(0, max_period, "idle_minp_%s_%s" % (tc, d))
            model.Add(min_local == max_period - max_inv)
            span = model.NewIntVar(0, max_period + 1, "idle_span_%s_%s" % (tc, d))
            model.Add(span == 0).OnlyEnforceIf(has_any.Not())
            model.Add(span == max_local - min_local + 1).OnlyEnforceIf(has_any)
            gaps = model.NewIntVar(0, max_period + 1, "idle_gaps_%s_%s" % (tc, d))
            model.Add(gaps == 0).OnlyEnforceIf(has_any.Not())
            model.Add(gaps == span - used).OnlyEnforceIf(has_any)
            penalties.append(gaps)
    if not penalties:
        return None
    total = model.NewIntVar(0, len(penalties) * (max_period + 1), "idle_total")
    model.Add(total == sum(penalties))
    return total


def _room_change(ctx):
    days = _days(ctx)
    model = ctx.model
    penalties = []
    for grp, sessions in ctx.sessions_by_group.items():
        if not sessions:
            continue
        sids = [s["id"] for s in sessions]
        for d, globals_in_day in days.items():
            day_starts = set(globals_in_day)
            on_day_terms = []
            for sid in sids:
                for t in ctx.valid_starts.get(sid, []):
                    if t in day_starts:
                        for rcode in ctx.candidate_resources.get(sid, []):
                            x = ctx.X.get((sid, t, rcode))
                            if x is not None:
                                on_day_terms.append(x)
            if not on_day_terms:
                continue
            has_day = model.NewBoolVar("rc_any_%s_%s" % (grp, d))
            model.AddMaxEquality(has_day, on_day_terms)
            room_used = []
            for r in ctx.resources:
                rcode = r["code"]
                terms = []
                for sid in sids:
                    for t in ctx.valid_starts.get(sid, []):
                        if t in day_starts:
                            x = ctx.X.get((sid, t, rcode))
                            if x is not None:
                                terms.append(x)
                if not terms:
                    continue
                b = model.NewBoolVar("rc_room_%s_%s_%s" % (grp, d, rcode))
                model.AddMaxEquality(b, terms)
                room_used.append(b)
            if not room_used:
                continue
            num_rooms = model.NewIntVar(0, len(room_used), "rc_num_%s_%s" % (grp, d))
            model.Add(num_rooms == sum(room_used))
            extra = model.NewIntVar(0, len(room_used), "rc_extra_%s_%s" % (grp, d))
            model.Add(extra == 0).OnlyEnforceIf(has_day.Not())
            model.Add(extra == num_rooms - 1).OnlyEnforceIf(has_day)
            penalties.append(extra)
    if not penalties:
        return None
    total = model.NewIntVar(0, len(penalties) * len(ctx.resources), "rc_total")
    model.Add(total == sum(penalties))
    return total


def _compact_schedule(ctx):
    days = _days(ctx)
    model = ctx.model
    penalties = []
    for grp, sessions in ctx.sessions_by_group.items():
        if not sessions:
            continue
        sids = [s["id"] for s in sessions]
        day_used = []
        for d, globals_in_day in days.items():
            day_starts = set(globals_in_day)
            terms = []
            for sid in sids:
                for t in ctx.valid_starts.get(sid, []):
                    if t in day_starts:
                        for rcode in ctx.candidate_resources.get(sid, []):
                            x = ctx.X.get((sid, t, rcode))
                            if x is not None:
                                terms.append(x)
            if not terms:
                continue
            b = model.NewBoolVar("cmp_day_%s_%s" % (grp, d))
            model.AddMaxEquality(b, terms)
            day_used.append(b)
        if not day_used:
            continue
        cnt = model.NewIntVar(0, len(day_used), "cmp_cnt_%s" % grp)
        model.Add(cnt == sum(day_used))
        penalties.append(cnt)
    if not penalties:
        return None
    total = model.NewIntVar(0, len(penalties) * len(days), "cmp_total")
    model.Add(total == sum(penalties))
    return total


def _teacher_load_balance(ctx):
    days = _days(ctx)
    model = ctx.model
    cap = _max_periods_per_day(ctx)
    penalties = []
    for tc, sessions in ctx.sessions_by_teacher.items():
        if not sessions:
            continue
        sids = [s["id"] for s in sessions]
        daily_loads = []
        for d, globals_in_day in days.items():
            busy_list = []
            for g in globals_in_day:
                terms = [ctx.occ[(sid, g)] for sid in sids if (sid, g) in ctx.occ]
                if not terms:
                    continue
                b = model.NewBoolVar("tlb_busy_%s_%s_%s" % (tc, d, ctx.horizon[g]["period"]))
                model.AddMaxEquality(b, terms)
                busy_list.append(b)
            load = model.NewIntVar(0, max(len(busy_list), 1), "tlb_load_%s_%s" % (tc, d))
            if busy_list:
                model.Add(load == sum(busy_list))
            else:
                model.Add(load == 0)
            daily_loads.append(load)
        if len(daily_loads) < 2:
            continue
        hi = model.NewIntVar(0, cap, "tlb_hi_%s" % tc)
        lo = model.NewIntVar(0, cap, "tlb_lo_%s" % tc)
        model.AddMaxEquality(hi, daily_loads)
        model.AddMinEquality(lo, daily_loads)
        spread = model.NewIntVar(0, cap, "tlb_spread_%s" % tc)
        model.Add(spread == hi - lo)
        penalties.append(spread)
    if not penalties:
        return None
    total = model.NewIntVar(0, len(penalties) * cap, "tlb_total")
    model.Add(total == sum(penalties))
    return total


_BUILDERS = (
    ("idle_teacher", _idle_teacher),
    ("room_change", _room_change),
    ("compact_schedule", _compact_schedule),
    ("teacher_load_balance", _teacher_load_balance),
)


def build_objective(ctx, weights, rule_terms):
    merged = merge_weights(weights)
    terms = list(rule_terms)
    for key, fn in _BUILDERS:
        weight = merged.get(key, 0) or 0
        if weight <= 0:
            continue
        pen = fn(ctx)
        if pen is None:
            continue
        ctx.record_soft(_default_rule(key, weight), pen, "default objective " + key)
        terms.append(weight * pen)
    return terms
