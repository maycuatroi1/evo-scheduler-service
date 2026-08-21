from ortools.sat.python import cp_model

from scheduler import horizon as horizon_config
from scheduler.solver.context import BuildContext
from scheduler.solver.constraints import apply_rule
from scheduler.solver.result import SolveResult, Assignment, RulePenalty
from scheduler.solver import feasibility, objectives

DEFAULT_MAX_TIME_SECONDS = 120.0
DEFAULT_SEED = 42

# Dữ liệu tự mâu thuẫn: không gọi solver vì không có lời giải nào tồn tại.
STATUS_DATA_INFEASIBLE = "DATA_INFEASIBLE"


def _failure_message(status_name, hard_count, soft_count):
    if status_name == "INFEASIBLE":
        return (
            "Không có phương án nào thoả mãn hết ràng buộc cứng "
            "(%d ràng buộc cứng, %d ràng buộc mềm). Hãy giảm tải cho lớp và "
            "giáo viên, hoặc mở rộng số tiết của thời khoá biểu." % (hard_count, soft_count)
        )
    if status_name == "UNKNOWN":
        return (
            "Bộ giải hết thời gian trước khi tìm được phương án nào. Hãy tăng "
            "thời gian giải hoặc giảm quy mô dữ liệu."
        )
    return "Bộ giải dừng với trạng thái %s (%d ràng buộc cứng, %d ràng buộc mềm)." % (
        status_name,
        hard_count,
        soft_count,
    )


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
        # Ràng buộc cá nhân; None nghĩa là không áp cho người này
        "max_periods_per_session": getattr(
            teacher, "max_periods_per_session", None
        ),
        "min_periods_per_session": getattr(
            teacher, "min_periods_per_session", None
        ),
        "days_off_per_week": getattr(teacher, "days_off_per_week", None),
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
    cfg = (getattr(tenant, "config_json", None) or {}).get("horizon")
    if isinstance(cfg, list) and cfg:
        return _normalize_horizon(cfg)
    return horizon_config.build(cfg)


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
    """Dựng biến theo mô hình khoảng thời gian.

    Mỗi buổi có một biến tiết bắt đầu và một biến chọn tài nguyên, thay cho
    tích Descartes buổi x tiết x tài nguyên. Cách cũ sinh hàng trăm nghìn biến
    bool trên dữ liệu thật và bộ giải không kết luận nổi.
    """
    model = ctx.model
    max_period = max((ts["period"] for ts in ctx.horizon), default=0)
    max_day = max((ts["day"] for ts in ctx.horizon), default=0)
    for s in ctx.sessions:
        sid = s["id"]
        dur = int(s["duration_slots"])
        valid = [t for t in range(ctx.num_timeslots) if ctx.same_day_run(t, dur)]
        ctx.valid_starts[sid] = valid
        candidates = feasibility.candidate_resources(ctx.resources, s)
        if not candidates:
            # Không có tài nguyên đúng loại: giữ lại toàn bộ để mô hình không
            # vô nghiệm câm lặng. Bản kiểm tra khả thi đã báo trường hợp này.
            candidates = [r["code"] for r in ctx.resources]
        locked_code = s.get("assigned_resource_code")
        if s.get("is_locked") and locked_code in ctx.resources_by_code:
            if locked_code not in candidates:
                candidates = candidates + [locked_code]
        ctx.candidate_resources[sid] = candidates

        if not valid or not candidates:
            ctx.blockers.append(
                "Buổi %s không có tiết hay tài nguyên nào hợp lệ."
                % (s.get("code") or sid)
            )
            ctx.start_timeslot[sid] = model.NewIntVar(0, 0, f"st_{sid}")
            ctx.start_period[sid] = model.NewIntVar(0, 0, f"sp_{sid}")
            ctx.start_day[sid] = model.NewIntVar(0, 0, f"sd_{sid}")
            continue

        st_var = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(valid), f"st_{sid}"
        )
        ctx.start_timeslot[sid] = st_var
        ctx.interval[sid] = model.NewIntervalVar(
            st_var, dur, st_var + dur, f"iv_{sid}"
        )

        start_lits = []
        for t in valid:
            lit = model.NewBoolVar(f"b_{sid}_{t}")
            ctx.start_lit[(sid, t)] = lit
            start_lits.append(lit)
        model.AddExactlyOne(start_lits)
        model.Add(st_var == sum(t * ctx.start_lit[(sid, t)] for t in valid))

        sp_var = model.NewIntVar(0, max_period, f"sp_{sid}")
        model.Add(
            sp_var
            == sum(ctx.horizon[t]["period"] * ctx.start_lit[(sid, t)] for t in valid)
        )
        ctx.start_period[sid] = sp_var
        sd_var = model.NewIntVar(0, max_day, f"sd_{sid}")
        model.Add(
            sd_var
            == sum(ctx.horizon[t]["day"] * ctx.start_lit[(sid, t)] for t in valid)
        )
        ctx.start_day[sid] = sd_var

        # Buổi thực tập và buổi ngoài trường chặn lớp nhưng không chiếm
        # phòng nào, nên không dựng biến chọn phòng cho chúng. Nếu vẫn ép
        # AddExactlyOne thì mô hình sẽ vô nghiệm dù thực tế không cần phòng.
        if not s.get("consumes_resources", True):
            continue

        res_lits = []
        for rcode in candidates:
            lit = model.NewBoolVar(f"r_{sid}_{rcode}")
            ctx.assign[(sid, rcode)] = lit
            ctx.res_interval[(sid, rcode)] = model.NewOptionalIntervalVar(
                st_var, dur, st_var + dur, lit, f"riv_{sid}_{rcode}"
            )
            res_lits.append(lit)
        model.AddExactlyOne(res_lits)

    for s in ctx.sessions:
        sid = s["id"]
        dur = int(s["duration_slots"])
        st_var = ctx.start_timeslot.get(sid)
        pre_assigned = s.get("teacher_codes", [])
        if pre_assigned:
            ctx.eligible_teachers[sid] = []
            if sid in ctx.interval:
                for tc in pre_assigned:
                    ctx.teacher_interval[(sid, tc)] = ctx.interval[sid]
            continue
        module_code = s.get("module_code")
        eligible = list(ctx.teacher_module_map.get(module_code, []))
        ctx.eligible_teachers[sid] = eligible
        for tc in eligible:
            lit = model.NewBoolVar(f"y_{sid}_{tc}")
            ctx.Y[(sid, tc)] = lit
            if st_var is not None and sid in ctx.interval:
                ctx.teacher_interval[(sid, tc)] = model.NewOptionalIntervalVar(
                    st_var, dur, st_var + dur, lit, f"tiv_{sid}_{tc}"
                )
        if eligible:
            model.AddExactlyOne(ctx.Y[(sid, tc)] for tc in eligible)


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
        start_lit = ctx.start_lit.get((sid, t_idx))
        res_lit = ctx.assign.get((sid, rcode))
        if start_lit is None or res_lit is None:
            # Khoá trỏ vào tiết hoặc tài nguyên không dựng được biến. Ép hết
            # về 0 sẽ làm mô hình vô nghiệm mà không nói lý do, nên bỏ khoá và
            # để buổi này được xếp tự do.
            ctx.warnings.append(
                "Buổi %s bị khoá vào vị trí không hợp lệ nên khoá đã bị bỏ qua."
                % (s.get("code") or sid)
            )
            continue
        ctx.model.Add(start_lit == 1)
        ctx.model.Add(res_lit == 1)


def _resource_overlap(ctx):
    ctx.enforce_resource_capacity()


# Trên bao nhiêu nhóm ứng viên phân biệt thì thôi thêm ràng buộc dư thừa.
MAX_REDUNDANT_POOLS = 24


def _redundant_pool_capacity(ctx):
    """Chặn trước số buổi cùng lúc trên từng nhóm tài nguyên dùng chung.

    Ràng buộc này suy ra được từ các ràng buộc đã có nên không đổi tập nghiệm,
    nhưng nó nói thẳng cho bộ giải điều mà kiểm tra khả thi vẫn kiểm: các buổi
    chỉ xếp được vào một nhóm phòng hẹp thì không thể đông hơn nhóm đó. Thiếu
    nó, bộ giải phải mò ra cùng kết luận qua từng phòng một.
    """
    pools = {}
    for s in ctx.sessions:
        sid = s["id"]
        if sid not in ctx.interval:
            continue
        candidates = frozenset(ctx.candidate_resources.get(sid, ()))
        if not candidates or len(candidates) >= len(ctx.resources):
            continue
        pools.setdefault(candidates, []).append(sid)
    if not pools or len(pools) > MAX_REDUNDANT_POOLS:
        return
    for pool, own_sids in pools.items():
        capacity = sum(
            int(ctx.resources_by_code[code].get("available_quantity", 1) or 1)
            for code in pool
            if code in ctx.resources_by_code
        )
        if capacity <= 0:
            continue
        sids = set(own_sids)
        for other, other_sids in pools.items():
            if other is not pool and other <= pool:
                sids.update(other_sids)
        intervals = [ctx.interval[sid] for sid in sorted(sids)]
        if len(intervals) > capacity:
            ctx.model.AddCumulative(intervals, [1] * len(intervals), capacity)


ZERO_WEIGHTS = {"idle_teacher": 0, "room_change": 0, "compact_schedule": 0, "teacher_load_balance": 0}


def _apply_rules(ctx, data):
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
    return objective_terms, hard_count, soft_count, skipped


def _assemble(data, weights, with_objective=True):
    """Dựng một mô hình hoàn chỉnh và trả về mọi thứ cần để giải nó."""
    model = cp_model.CpModel()
    ctx = BuildContext(model, data)
    _build_variables(ctx)
    _apply_locked(ctx)
    if ctx.blockers:
        return model, ctx, [], 0, 0, []
    _resource_overlap(ctx)
    _redundant_pool_capacity(ctx)
    objective_terms, hard_count, soft_count, skipped = _apply_rules(ctx, data)
    if with_objective:
        objective_terms = objectives.build_objective(ctx, weights, objective_terms)
    else:
        objective_terms = []
    return model, ctx, objective_terms, hard_count, soft_count, skipped


def _new_solver(limit, seed, verbose):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(float(limit), 1.0)
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = int(seed)
    solver.parameters.log_search_progress = bool(verbose)
    return solver


class _StopWhenAsked(cp_model.CpSolverSolutionCallback):
    """Dừng bộ giải khi người dùng bấm Dừng, nhưng giữ nghiệm đã tìm được.

    CP-SAT chỉ kiểm tra được yêu cầu dừng mỗi khi tìm ra một nghiệm mới,
    nên lệnh dừng có độ trễ tới nghiệm kế tiếp. Đó là đánh đổi chấp nhận
    được: dừng ngay giữa chừng mà chưa có nghiệm nào thì cũng không dùng
    được kết quả.
    """

    def __init__(self, should_stop):
        super().__init__()
        self._should_stop = should_stop
        self.stopped = False
        self.solutions = 0

    def on_solution_callback(self):
        self.solutions += 1
        try:
            if self._should_stop():
                self.stopped = True
                self.StopSearch()
        except Exception:
            # Lỗi khi hỏi trạng thái dừng không được làm hỏng lần giải
            pass


def _run(solver, model, should_stop):
    """Gọi bộ giải, gắn callback dừng nếu có."""
    if should_stop is None:
        return solver.StatusName(solver.Solve(model)), None
    cb = _StopWhenAsked(should_stop)
    status = solver.StatusName(solver.Solve(model, cb))
    return status, cb


def _hint_from(model, ctx, source_ctx, solver):
    """Chép nghiệm của mô hình khả thi sang mô hình có hàm mục tiêu."""
    pairs = (
        (source_ctx.start_lit, ctx.start_lit),
        (source_ctx.assign, ctx.assign),
        (source_ctx.Y, ctx.Y),
    )
    for source_map, target_map in pairs:
        for key, lit in source_map.items():
            target = target_map.get(key)
            if target is not None and solver.Value(lit) == 1:
                model.AddHint(target, 1)


def _solve_in_two_phases(
    data,
    model,
    ctx,
    objective_terms,
    max_time_seconds,
    seed,
    verbose,
    should_stop=None,
):
    """Tìm một phương án khả thi trước, rồi mới tối ưu từ chính phương án đó.

    Trên dữ liệu thật, gắn hàm mục tiêu ngay từ đầu khiến bộ giải hết giờ mà
    chưa có phương án nào. Mô hình không hàm mục tiêu nhỏ hơn hẳn và bộ giải
    dừng ngay khi tìm được phương án đầu tiên, nên pha một về đích nhanh;
    nghiệm của nó vừa làm gợi ý cho pha hai vừa là phương án dự phòng nếu pha
    hai không kịp.
    """
    total = float(max_time_seconds)
    if not objective_terms:
        solver = _new_solver(total, seed, verbose)
        status, _cb = _run(solver, model, should_stop)
        return solver, ctx, status, float(solver.WallTime())

    feas_model, feas_ctx, _, _, _, _ = _assemble(data, ZERO_WEIGHTS, with_objective=False)
    first = _new_solver(total, seed, verbose)
    first_status, first_cb = _run(first, feas_model, should_stop)
    elapsed = float(first.WallTime())
    if first_status not in ("OPTIMAL", "FEASIBLE"):
        # Vô nghiệm hoặc hết giờ ở pha một thì hàm mục tiêu cũng không cứu được.
        return first, feas_ctx, first_status, elapsed

    # Người dùng đã bấm Dừng ở pha một: giữ nghiệm khả thi vừa tìm được,
    # không tốn thêm thời gian cho pha tối ưu.
    if first_cb is not None and first_cb.stopped:
        return first, feas_ctx, "FEASIBLE", elapsed

    _hint_from(model, ctx, feas_ctx, first)
    model.Minimize(sum(objective_terms))
    remaining = total - elapsed
    if remaining < 1.0:
        return first, feas_ctx, "FEASIBLE", elapsed
    second = _new_solver(remaining, seed, verbose)
    second_status, _cb2 = _run(second, model, should_stop)
    elapsed += float(second.WallTime())
    if second_status in ("OPTIMAL", "FEASIBLE"):
        return second, ctx, second_status, elapsed
    # Pha hai không kịp cải thiện: giữ nguyên phương án của pha một.
    return first, feas_ctx, "FEASIBLE", elapsed


def build_and_solve(data, max_time_seconds=DEFAULT_MAX_TIME_SECONDS, seed=DEFAULT_SEED, verbose=False, persist_callback=None, weights=None, skip_preflight=False, should_stop=None):
    if not data.get("sessions"):
        return SolveResult(status="UNKNOWN", objective_value=0.0, solver_log="no sessions")
    issues = [] if skip_preflight else feasibility.check(data)
    blocking = feasibility.blocking(issues)
    if blocking:
        return SolveResult(
            status=STATUS_DATA_INFEASIBLE,
            objective_value=0.0,
            violations=feasibility.messages(blocking),
            diagnostics=issues,
            solver_log="preflight",
        )
    model, ctx, objective_terms, hard_count, soft_count, skipped = _assemble(data, weights)
    if ctx.blockers:
        return SolveResult(
            status=STATUS_DATA_INFEASIBLE,
            objective_value=0.0,
            violations=list(ctx.blockers),
            diagnostics=issues,
            solver_log="preflight",
        )
    num_constraints = len(model.Proto().constraints)
    solver, ctx, status_name, wall_time = _solve_in_two_phases(
        data,
        model,
        ctx,
        objective_terms,
        max_time_seconds,
        seed,
        verbose,
        should_stop=should_stop,
    )
    result = SolveResult(
        status=status_name,
        objective_value=float(solver.ObjectiveValue()) if status_name in ("OPTIMAL", "FEASIBLE") else 0.0,
        num_constraints=num_constraints,
        num_booleans=solver.NumBooleans(),
        wall_time=wall_time,
        diagnostics=issues,
    )
    result.violations.extend(ctx.warnings)
    if status_name not in ("OPTIMAL", "FEASIBLE"):
        result.violations.insert(0, _failure_message(status_name, hard_count, soft_count))
        result.violations.extend(feasibility.messages(issues))
        if skipped:
            result.violations.extend(skipped)
        return result
    for s in ctx.sessions:
        sid = s["id"]
        chosen_t, chosen_r = ctx.solution_for(solver, sid)
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
