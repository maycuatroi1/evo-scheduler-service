from ortools.sat.python import cp_model

from scheduler.solver.context import BuildContext
from scheduler.solver.constraints import apply_rule
from scheduler.solver.result import SolveResult, Assignment, RulePenalty
from scheduler.solver import objectives

DEFAULT_MAX_TIME_SECONDS = 10.0
DEFAULT_SEED = 42


def _rule_to_dict(rule):
    if isinstance(rule, dict):
        return rule
    return {
        "id": getattr(rule, "id", 0),
        "type": getattr(rule, "type", None),
        "params_json": getattr(rule, "params_json", None) or {},
        "scope_json": getattr(rule, "scope_json", None) or {},
        "hardness": getattr(rule, "hardness", "hard"),
        "weight": getattr(rule, "weight", 1) or 1,
        "active": getattr(rule, "active", True),
    }


def _session_to_dict(session):
    teacher_codes = []
    for t in session.assigned_teachers.all():
        teacher_codes.append(t.code)
    group = getattr(session, "student_group", None)
    return {
        "id": session.id,
        "code": f"{session.module.code}/{session.session_type}/{session.id}",
        "session_type": session.session_type,
        "tier": getattr(session, "tier", None),
        "duration_slots": int(session.duration_slots or 1),
        "group_size": int(getattr(group, "size", 0) or 0) if group else 0,
        "group_code": getattr(group, "code", None) if group else None,
        "module_code": session.module.code,
        "teacher_codes": teacher_codes,
        "is_locked": bool(getattr(session, "is_locked", False)),
        "assigned_timeslot": getattr(session, "assigned_timeslot", None),
        "assigned_resource_code": getattr(getattr(session, "assigned_resource", None), "code", None),
    }


def _resource_to_dict(resource):
    return {
        "id": resource.id,
        "code": resource.code,
        "type": resource.type,
        "capacity": int(resource.capacity or 0),
        "available_quantity": int(resource.available_quantity or 1),
    }


def _teacher_to_dict(teacher):
    return {
        "id": teacher.id,
        "code": teacher.code,
        "quota_standard_hours": teacher.quota_standard_hours,
    }


def extract(schedule, constraint_rules, data=None):
    data = dict(data or {})
    tenant = schedule.tenant
    horizon = data.get("horizon")
    if not horizon:
        horizon = _default_horizon(tenant)
    sessions_qs = _sessions_for(schedule, tenant)
    sessions = [_session_to_dict(s) for s in sessions_qs]
    resources = [_resource_to_dict(r) for r in tenant.resources.all()]
    teachers = [_teacher_to_dict(t) for t in tenant.teachers.all()]
    rules = [_rule_to_dict(r) for r in constraint_rules if _rule_to_dict(r).get("active", True)]
    data.setdefault("hours_per_slot", 1.0)
    data["horizon"] = horizon
    data["sessions"] = sessions
    data["resources"] = resources
    data["teachers"] = teachers
    data["rules"] = rules
    data["tenant_code"] = tenant.code
    tm_map = {}
    for tm in tenant.teacher_modules.select_related("teacher", "module"):
        tm_map.setdefault(tm.module.code, []).append(tm.teacher.code)
    data["teacher_module_map"] = tm_map
    return data


def _sessions_for(schedule, tenant):
    qs = tenant.sessions.select_related("module", "student_group", "assigned_resource")
    qs = qs.prefetch_related("assigned_teachers")
    if getattr(schedule, "tier", None):
        qs = qs.filter(tier=schedule.tier)
    return qs


def _default_horizon(tenant):
    cfg = (tenant.config_json or {}).get("horizon")
    if cfg:
        return _normalize_horizon(cfg)
    days = [
        ("monday", 0),
        ("tuesday", 1),
        ("wednesday", 2),
        ("thursday", 3),
        ("friday", 4),
        ("saturday", 5),
    ]
    periods_per_day = 5
    morning_count = 2
    horizon = []
    idx = 0
    for name, d in days:
        for p in range(periods_per_day):
            horizon.append({
                "index": idx,
                "day": d,
                "period": p,
                "day_name": name,
                "is_morning": p < morning_count,
            })
            idx += 1
    return horizon


def _normalize_horizon(cfg):
    if isinstance(cfg, list):
        horizon = []
        for i, ts in enumerate(cfg):
            item = dict(ts)
            item.setdefault("index", i)
            item.setdefault("is_morning", item.get("period", 0) < item.get("morning_count", 2))
            horizon.append(item)
        return horizon
    days = cfg.get("days", [])
    periods_per_day = cfg.get("periods_per_day", 5)
    morning_count = cfg.get("morning_count", 2)
    horizon = []
    idx = 0
    for d in days:
        if isinstance(d, dict):
            name, dnum = d.get("name"), d.get("day")
        else:
            name, dnum = d, len(horizon)
        for p in range(periods_per_day):
            horizon.append({
                "index": idx,
                "day": dnum,
                "period": p,
                "day_name": name,
                "is_morning": p < morning_count,
            })
            idx += 1
    return horizon


def _build_variables(ctx):
    model = ctx.model
    for s in ctx.sessions:
        sid = s["id"]
        dur = s["duration_slots"]
        valid = [t for t in range(ctx.num_timeslots) if ctx.same_day_run(t, dur)]
        ctx.valid_starts[sid] = valid
        candidates = [r["code"] for r in ctx.resources]
        ctx.candidate_resources[sid] = candidates
        for t in valid:
            for rcode in candidates:
                ctx.X[(sid, t, rcode)] = model.NewBoolVar(f"x_{sid}_{t}_{rcode}")
    for s in ctx.sessions:
        sid = s["id"]
        valid = ctx.valid_starts[sid]
        all_vars = [ctx.X[(sid, t, r)] for t in valid for r in ctx.candidate_resources[sid] if (sid, t, r) in ctx.X]
        if all_vars:
            model.Add(sum(all_vars) == 1)
        else:
            model.Add(sum([]) == 1)
        st_var = model.NewIntVar(0, max(ctx.num_timeslots - 1, 0), f"st_{sid}")
        if valid:
            model.Add(st_var == sum(t * ctx.X[(sid, t, r)] for t in valid for r in ctx.candidate_resources[sid] if (sid, t, r) in ctx.X))
        else:
            model.Add(st_var == 0)
        ctx.start_timeslot[sid] = st_var
        period_terms = []
        for t in valid:
            ts = ctx.horizon[t]
            for r in ctx.candidate_resources[sid]:
                x = ctx.X.get((sid, t, r))
                if x is not None:
                    period_terms.append(ts["period"] * x)
        max_period = max((ts["period"] for ts in ctx.horizon), default=0)
        sp_var = model.NewIntVar(0, max_period, f"sp_{sid}")
        if period_terms:
            model.Add(sp_var == sum(period_terms))
        else:
            model.Add(sp_var == 0)
        ctx.start_period[sid] = sp_var
        day_terms = []
        for t in valid:
            ts = ctx.horizon[t]
            for r in ctx.candidate_resources[sid]:
                x = ctx.X.get((sid, t, r))
                if x is not None:
                    day_terms.append(ts["day"] * x)
        max_day = max((ts["day"] for ts in ctx.horizon), default=0)
        sd_var = model.NewIntVar(0, max_day, f"sd_{sid}")
        if day_terms:
            model.Add(sd_var == sum(day_terms))
        else:
            model.Add(sd_var == 0)
        ctx.start_day[sid] = sd_var
        for p in range(ctx.num_timeslots):
            cover_terms = []
            for t in valid:
                if p in ctx.covers(t, s["duration_slots"]):
                    for r in ctx.candidate_resources[sid]:
                        x = ctx.X.get((sid, t, r))
                        if x is not None:
                            cover_terms.append(x)
            occ_var = model.NewBoolVar(f"occ_{sid}_{p}")
            if cover_terms:
                model.Add(occ_var == sum(cover_terms))
            else:
                model.Add(occ_var == 0)
            ctx.occ[(sid, p)] = occ_var

    model = ctx.model
    for s in ctx.sessions:
        sid = s["id"]
        pre_assigned = s.get("teacher_codes", [])
        if pre_assigned:
            ctx.eligible_teachers[sid] = []
            continue
        module_code = s.get("module_code")
        eligible = list(ctx.teacher_module_map.get(module_code, []))
        ctx.eligible_teachers[sid] = eligible
        for tc in eligible:
            ctx.Y[(sid, tc)] = model.NewBoolVar(f"y_{sid}_{tc}")
        if eligible:
            model.Add(sum(ctx.Y[(sid, tc)] for tc in eligible) == 1)


def _apply_locked(ctx):
    for s in ctx.sessions:
        sid = s["id"]
        locked_ts = s.get("assigned_timeslot")
        if not (s.get("is_locked") or locked_ts):
            continue
        if isinstance(locked_ts, dict):
            t_idx = locked_ts.get("index")
        else:
            t_idx = locked_ts
        rcode = s.get("assigned_resource_code")
        if rcode is None:
            continue
        for (sid2, t, rcode2), x in ctx.X.items():
            if sid2 != sid:
                continue
            if t == t_idx and rcode2 == rcode:
                ctx.model.Add(x == 1)
            else:
                ctx.model.Add(x == 0)


def _resource_overlap(ctx):
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


def build_and_solve(data, max_time_seconds=DEFAULT_MAX_TIME_SECONDS, seed=DEFAULT_SEED, verbose=False, persist_callback=None, weights=None):
    model = cp_model.CpModel()
    ctx = BuildContext(model, data)
    if not ctx.sessions:
        return SolveResult(status="UNKNOWN", objective_value=0.0, solver_log="no sessions")
    _build_variables(ctx)
    _apply_locked(ctx)
    _resource_overlap(ctx)
    objective_terms = []
    hard_count = 0
    soft_count = 0
    skipped = []
    for rule in data.get("rules", []):
        if not rule.get("active", True):
            continue
        try:
            term = apply_rule(ctx, rule)
        except Exception as exc:
            skipped.append(f"{rule.get('type')} rule#{rule.get('id')}: {exc}")
            continue
        if term is not None:
            objective_terms.append(term)
            soft_count += 1
        else:
            hard_count += 1
    objective_terms = objectives.build_objective(ctx, weights, objective_terms)
    if objective_terms:
        model.Minimize(sum(objective_terms))
    num_constraints = len(model.Proto().constraints)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(max_time_seconds)
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = int(seed)
    solver.parameters.log_search_progress = bool(verbose)
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    result = SolveResult(
        status=status_name,
        objective_value=float(solver.ObjectiveValue()) if status_name in ("OPTIMAL", "FEASIBLE") else 0.0,
        num_constraints=num_constraints,
        num_booleans=solver.NumBooleans(),
        wall_time=float(solver.WallTime()),
    )
    if status_name not in ("OPTIMAL", "FEASIBLE"):
        result.violations = [f"model is {status_name}; check hard rules (hard={hard_count}, soft={soft_count})"]
        if skipped:
            result.violations.extend(skipped)
        return result
    for s in ctx.sessions:
        sid = s["id"]
        chosen_t = None
        chosen_r = None
        for t in ctx.valid_starts.get(sid, []):
            for rcode in ctx.candidate_resources.get(sid, []):
                x = ctx.X.get((sid, t, rcode))
                if x is not None and solver.Value(x) == 1:
                    chosen_t = t
                    chosen_r = rcode
                    break
            if chosen_t is not None:
                break
        if chosen_t is None:
            continue
        ts = ctx.horizon[chosen_t]
        teacher_codes = list(s.get("teacher_codes", []))
        auto_assigned = False
        if not teacher_codes:
            for tc in ctx.eligible_teachers.get(sid, []):
                y = ctx.Y.get((sid, tc))
                if y is not None and solver.Value(y) == 1:
                    teacher_codes = [tc]
                    auto_assigned = True
                    break
        result.assignments.append(Assignment(
            session_id=sid,
            session_code=s["code"],
            timeslot_index=chosen_t,
            day=ts["day"],
            period=ts["period"],
            day_name=ts.get("day_name", ""),
            resource_code=chosen_r,
            teacher_codes=teacher_codes,
            auto_assigned_teachers=auto_assigned,
        ))
    for rule, var, detail in ctx.soft_records:
        value = int(solver.Value(var))
        result.penalties.append(RulePenalty(
            rule_id=rule.get("id", 0),
            rule_type=rule.get("type"),
            hardness=rule.get("hardness", "soft"),
            weight=int(rule.get("weight", 1) or 1),
            penalty=value * int(rule.get("weight", 1) or 1),
            detail=detail,
        ))
        if value > 0:
            result.violations.append(f"soft {rule.get('type')} rule#{rule.get('id')} violated {value} (weight={rule.get('weight')}) {detail}")
    if skipped:
        result.violations.extend(skipped)
    if persist_callback is not None:
        persist_callback(result)
    return result


def solve(schedule, constraint_rules, data=None, max_time_seconds=DEFAULT_MAX_TIME_SECONDS, seed=DEFAULT_SEED, verbose=False, persist=False, weights=None):
    data = extract(schedule, constraint_rules, data)
    persist_cb = None
    if persist:
        from scheduler.models import Resource, Teacher

        def persist_cb(result):
            res_by_code = {r.code: r for r in Resource.objects.filter(tenant=schedule.tenant)}
            teacher_by_code = {t.code: t for t in Teacher.objects.filter(tenant=schedule.tenant)}
            sessions = {s.id: s for s in _sessions_for(schedule, schedule.tenant)}
            for a in result.assignments:
                sess = sessions.get(a.session_id)
                if not sess:
                    continue
                ts = data["horizon"][a.timeslot_index]
                sess.assigned_timeslot = {
                    "index": a.timeslot_index,
                    "day": a.day,
                    "period": a.period,
                    "day_name": a.day_name,
                }
                sess.assigned_resource = res_by_code.get(a.resource_code)
                sess.save(update_fields=["assigned_timeslot", "assigned_resource"])
                if getattr(a, "auto_assigned_teachers", False) and a.teacher_codes:
                    teachers = [teacher_by_code[tc] for tc in a.teacher_codes if tc in teacher_by_code]
                    if teachers:
                        sess.assigned_teachers.set(teachers)
    return build_and_solve(data, max_time_seconds=max_time_seconds, seed=seed, verbose=verbose, persist_callback=persist_cb, weights=weights)
