import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from scheduler import horizon as horizon_config
from scheduler.models import Schedule
from scheduler.solver.engine import (
    DEFAULT_MAX_TIME_SECONDS,
    DEFAULT_SEED,
    _default_horizon,
    _normalize_horizon,
    _resource_to_dict,
    _teacher_to_dict,
    build_and_solve,
)
from scheduler.solver import feasibility
from scheduler.solver.objectives import merge_weights
from scheduler.solver.result import Assignment, SolveResult

TIER_MODE_KEY = "tier_mode"
TWO_TIER = "two_tier"
SINGLE_TIER = "single_tier"

CULTURE = "culture"
VOCATIONAL = "vocational"

CROSS_TIER_RULES = [
    {
        "id": -100,
        "type": "teacher_no_overlap",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -101,
        "type": "student_no_overlap",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -102,
        "type": "shared_resource_pool",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    # Ràng buộc đặc thù trường nghề — luôn áp, không cần khai báo
    {
        "id": -103,
        "type": "group_same_class",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -104,
        "type": "shift_by_grade",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -105,
        "type": "offsite_no_room",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -106,
        "type": "capacity_by_type",
        "hardness": "hard",
        "weight": 1,
        "active": True,
    },
    {
        "id": -107,
        "type": "teacher_limits",
        "hardness": "soft",
        "weight": 3,
        "active": True,
    },
]

@dataclass
class TierResult:
    tier: str
    status: str
    objective_value: float
    assignments: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    num_sessions: int = 0
    diagnostics: list = field(default_factory=list)


@dataclass
class OrchestratorResult:
    solve_job_id: str
    tier_mode: str
    status: str
    objective_value: float
    tier_results: list = field(default_factory=list)
    assignments: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


def _tenant_tier_mode(tenant) -> str:
    cfg = (tenant.config_json or {}).get(TIER_MODE_KEY)
    if cfg in (TWO_TIER, SINGLE_TIER):
        return cfg
    tiers = set(
        tenant.sessions.values_list("tier", flat=True)
        .exclude(tier__isnull=True)
        .exclude(tier="")
    )
    if CULTURE in tiers and VOCATIONAL in tiers:
        return TWO_TIER
    return SINGLE_TIER


HORIZON_KEYS = (
    "weeks",
    "days",
    "days_per_week",
    "periods_per_day",
    "morning_count",
)


def _build_horizon(cfg) -> list:
    if not cfg:
        return horizon_config.build(None)
    if isinstance(cfg, list):
        return _normalize_horizon(cfg)
    if isinstance(cfg, dict):
        if any(key in cfg for key in HORIZON_KEYS):
            return horizon_config.build(cfg)
        return _normalize_horizon(cfg)
    return _default_horizon(None)


def _tenant_horizon(tenant, key) -> list:
    cfg = (tenant.config_json or {})
    specific = cfg.get(key)
    if specific:
        return _build_horizon(specific)
    base = cfg.get("horizon")
    if base:
        return _build_horizon(base)
    return _build_horizon(None)


def _rule_dicts_for(tenant) -> list:
    out = []
    for r in tenant.constraint_rules.filter(active=True):
        out.append(
            {
                "id": r.id,
                "type": r.type,
                "params_json": r.params_json or {},
                "scope_json": r.scope_json or {},
                "hardness": r.hardness,
                "weight": r.weight or 1,
                "active": True,
            }
        )
    return out


def _session_dict(session) -> dict:
    teacher_codes = [t.code for t in session.assigned_teachers.all()]
    group = getattr(session, "student_group", None)
    res = getattr(session, "assigned_resource", None)
    ats = getattr(session, "assigned_timeslot", None)
    return {
        "id": session.id,
        "code": "%s/%s/%s" % (session.module.code, session.session_type, session.id),
        "session_type": session.session_type,
        "tier": getattr(session, "tier", None),
        "duration_slots": int(session.duration_slots or 1),
        "group_size": int(getattr(group, "size", 0) or 0) if group else 0,
        "group_code": getattr(group, "code", None) if group else None,
        "module_code": session.module.code,
        "teacher_codes": teacher_codes,
        "is_locked": bool(getattr(session, "is_locked", False)),
        "assigned_timeslot": ats,
        "assigned_resource_code": getattr(res, "code", None) if res else None,
        # Các lớp văn hoá mà buổi này chạm tới. Nhóm nghề gộp nhiều lớp thì
        # danh sách có nhiều phần tử; nhóm không thuộc hệ 9+ thì rỗng.
        "homeroom_codes": _homeroom_codes(group),
        # Ca được phép, suy từ ca văn hoá của lớp gốc.
        "allowed_shift": _allowed_shift(session, group),
        "hazardous": bool(getattr(group, "hazardous", False)) if group else False,
        "consumes_resources": _consumes(session),
    }


def _homeroom_codes(group):
    if group is None:
        return []
    try:
        return [h.code for h in group.homerooms.all()]
    except Exception:
        return []


def _allowed_shift(session, group):
    """Buổi văn hoá theo ca của lớp; buổi nghề theo ca bù.

    Lớp học cả ngày (khối 12) không bị giới hạn ca cho phần văn hoá.
    """
    if group is None:
        return "any"
    try:
        homes = list(group.homerooms.all())
    except Exception:
        return "any"
    if not homes:
        return "any"
    shifts = set()
    tier = getattr(session, "tier", None)
    for h in homes:
        if tier == "culture":
            shifts.add(h.culture_shift)
        else:
            shifts.add(h.vocational_shift())
    if len(shifts) != 1:
        return "any"
    only = shifts.pop()
    if only == "full_day":
        return "any"
    return "morning" if only == "morning" else "afternoon"


def _consumes(session):
    try:
        return bool(session.consumes_resources())
    except Exception:
        return True


def _locked_phantom(session, target_horizon) -> Optional[dict]:
    ats = getattr(session, "assigned_timeslot", None)
    if not ats:
        return None
    if isinstance(ats, dict):
        src_day = ats.get("day")
        src_period = ats.get("period")
        src_day_name = ats.get("day_name", "")
    else:
        return None
    target_idx = None
    for i, ts in enumerate(target_horizon):
        if ts.get("day") == src_day and ts.get("period") == src_period:
            target_idx = i
            break
    if target_idx is None:
        return None
    res = getattr(session, "assigned_resource", None)
    group = getattr(session, "student_group", None)
    teacher_codes = [t.code for t in session.assigned_teachers.all()]
    return {
        "id": -(int(session.id)),
        "code": "locked/%s/%s" % (getattr(session, "tier", "x"), session.id),
        "session_type": getattr(session, "session_type", "theory"),
        "tier": getattr(session, "tier", None),
        "duration_slots": int(getattr(session, "duration_slots", 1) or 1),
        "group_size": int(getattr(group, "size", 0) or 0) if group else 0,
        "group_code": getattr(group, "code", None) if group else None,
        "module_code": getattr(session.module, "code", "M"),
        "teacher_codes": teacher_codes,
        "is_locked": True,
        "assigned_timeslot": {
            "index": target_idx,
            "day": src_day,
            "period": src_period,
            "day_name": src_day_name,
        },
        "assigned_resource_code": getattr(res, "code", None) if res else None,
    }


def _pending_phantom(session) -> dict:
    """Buổi của khối giải trước, khi nó chưa được xếp vào đâu cả.

    Chỉ dùng cho bản kiểm tra khả thi: nó không nói được buổi sẽ nằm ở đâu,
    nhưng vẫn phải đếm vào nhu cầu phòng và nhu cầu tiết của lớp.
    """
    data = _session_dict(session)
    data["id"] = -(int(session.id))
    data["code"] = "pending/%s/%s" % (getattr(session, "tier", "x"), session.id)
    data["is_locked"] = False
    data["assigned_timeslot"] = None
    data["assigned_resource_code"] = None
    return data


def _build_data(tenant, session_dicts, horizon, rules, weights) -> dict:
    tm_map = {}
    for tm in tenant.teacher_modules.select_related("teacher", "module"):
        tm_map.setdefault(tm.module.code, []).append(tm.teacher.code)
    return {
        "tenant_code": tenant.code,
        "horizon": horizon,
        "sessions": session_dicts,
        "resources": [_resource_to_dict(r) for r in tenant.resources.all()],
        "teachers": [_teacher_to_dict(t) for t in tenant.teachers.all()],
        "rules": list(rules),
        "hours_per_slot": 1.0,
        "teacher_module_map": tm_map,
    }


def _fetch_sessions(tenant, tier=None) -> list:
    qs = tenant.sessions.select_related("module", "student_group", "assigned_resource")
    qs = qs.prefetch_related("assigned_teachers")
    if tier:
        qs = qs.filter(tier=tier)
    return list(qs)


def _persist_assignments(
    schedule, sessions_by_id, assignments, horizon, lock=False
) -> None:
    res_by_code = {r.code: r for r in schedule.tenant.resources.all()}
    teacher_by_code = {t.code: t for t in schedule.tenant.teachers.all()}
    fields = ["assigned_timeslot", "assigned_resource"]
    if lock:
        fields.append("is_locked")
    for a in assignments:
        sess = sessions_by_id.get(a.session_id)
        if not sess:
            continue
        ts = horizon[a.timeslot_index]
        sess.assigned_timeslot = {
            "index": a.timeslot_index,
            "day": a.day,
            "period": a.period,
            "day_name": a.day_name,
            "week": ts.get("week", 0),
        }
        sess.assigned_resource = res_by_code.get(a.resource_code)
        if lock:
            sess.is_locked = True
        sess.save(update_fields=fields)
        if getattr(a, "auto_assigned_teachers", False) and a.teacher_codes:
            teachers = [
                teacher_by_code[tc]
                for tc in a.teacher_codes
                if tc in teacher_by_code
            ]
            if teachers:
                sess.assigned_teachers.set(teachers)


def _solve_tier(
    tenant,
    session_dicts,
    horizon,
    rules,
    weights,
    max_time_seconds,
    seed,
    verbose,
    should_stop=None,
) -> SolveResult:
    if not session_dicts:
        return SolveResult(status="UNKNOWN", objective_value=0.0, solver_log="no sessions")
    data = _build_data(tenant, session_dicts, horizon, rules, weights)
    return build_and_solve(
        data,
        max_time_seconds=max_time_seconds,
        seed=seed,
        verbose=verbose,
        weights=weights,
        should_stop=should_stop,
    )


def preflight(schedule: Schedule, tenant: Any = None) -> dict:
    """Kiểm tra khả thi từng tier mà không chạy bộ giải.

    Dùng đúng dữ liệu và khung giờ mà `orchestrate` sẽ dùng, nên kết quả ở đây
    dự báo được lần chạy thật.
    """
    tenant = tenant or schedule.tenant
    tier_mode = _tenant_tier_mode(tenant)
    rules = _rule_dicts_for(tenant) + CROSS_TIER_RULES
    tiers = []

    if tier_mode == TWO_TIER:
        plan = ((CULTURE, "culture_horizon"), (VOCATIONAL, "vocational_horizon"))
    else:
        plan = ((None, "horizon"),)

    for tier, horizon_key in plan:
        horizon = _tenant_horizon(tenant, horizon_key)
        sessions = _fetch_sessions(tenant, tier=tier)
        session_dicts = [_session_dict(s) for s in sessions]
        if tier == VOCATIONAL:
            for cs in _fetch_sessions(tenant, tier=CULTURE):
                phantom = _locked_phantom(cs, horizon)
                if phantom is None:
                    # Buổi khối trước chưa được xếp vẫn sẽ chiếm phòng và chiếm
                    # tiết của lớp khi giải thật. Bỏ qua chúng thì bản kiểm tra
                    # báo khả thi rồi lần giải mới lộ ra thiếu chỗ.
                    phantom = _pending_phantom(cs)
                session_dicts.append(phantom)
        data = _build_data(tenant, session_dicts, horizon, rules, None)
        issues = feasibility.check(data)
        tiers.append(
            {
                "tier": tier or "all",
                "num_sessions": len(sessions),
                "total_slots": len(horizon),
                "issues": issues,
                "blocking_count": len(feasibility.blocking(issues)),
            }
        )

    blocking_total = sum(t["blocking_count"] for t in tiers)
    return {
        "tier_mode": tier_mode,
        "feasible": blocking_total == 0,
        "blocking_count": blocking_total,
        "tiers": tiers,
    }


def orchestrate(
    schedule: Schedule,
    tenant: Any = None,
    data: Optional[dict] = None,
    max_time_seconds: float = DEFAULT_MAX_TIME_SECONDS,
    seed: int = DEFAULT_SEED,
    verbose: bool = False,
    weights: Optional[dict] = None,
    should_stop=None,
) -> OrchestratorResult:
    tenant = tenant or schedule.tenant
    tier_mode = _tenant_tier_mode(tenant)
    solve_job_id = uuid.uuid4().hex

    def _tag(tier, issues):
        return [dict(issue, tier=tier) for issue in issues or []]

    if weights is None:
        weights = merge_weights(schedule.weights_json)
    rules = _rule_dicts_for(tenant) + CROSS_TIER_RULES

    schedule.status = Schedule.Status.SOLVING
    schedule.objective_value = None
    schedule.save(update_fields=["status", "objective_value"])

    tier_results: list = []
    all_assignments: list = []
    all_violations: list = []
    all_diagnostics: list = []
    objective_total = 0.0
    overall_status = Schedule.Status.SOLVED

    try:
        if tier_mode == TWO_TIER:
            culture_sessions = _fetch_sessions(tenant, tier=CULTURE)
            vocational_sessions = _fetch_sessions(tenant, tier=VOCATIONAL)

            culture_horizon = _tenant_horizon(tenant, "culture_horizon")
            culture_dicts = [_session_dict(s) for s in culture_sessions]
            culture_result = _solve_tier(
                tenant,
                culture_dicts,
                culture_horizon,
                rules,
                weights,
                max_time_seconds,
                seed,
                verbose,
                should_stop,
            )
            culture_by_id = {s.id: s for s in culture_sessions}
            _persist_assignments(
                schedule,
                culture_by_id,
                culture_result.assignments,
                culture_horizon,
                lock=True,
            )
            tier_results.append(
                TierResult(
                    tier=CULTURE,
                    status=culture_result.status,
                    objective_value=culture_result.objective_value,
                    assignments=list(culture_result.assignments),
                    violations=list(culture_result.violations),
                    num_sessions=len(culture_sessions),
                    diagnostics=_tag(CULTURE, culture_result.diagnostics),
                )
            )
            all_assignments.extend(culture_result.assignments)
            all_violations.extend(culture_result.violations)
            all_diagnostics.extend(_tag(CULTURE, culture_result.diagnostics))
            objective_total += float(culture_result.objective_value or 0.0)
            if not culture_result.is_feasible:
                overall_status = Schedule.Status.FAILED

            voc_horizon = _tenant_horizon(tenant, "vocational_horizon")
            voc_dicts = [_session_dict(s) for s in vocational_sessions]
            culture_sessions_refresh = _fetch_sessions(tenant, tier=CULTURE)
            for cs in culture_sessions_refresh:
                phantom = _locked_phantom(cs, voc_horizon)
                if phantom is not None:
                    voc_dicts.append(phantom)
            voc_result = _solve_tier(
                tenant,
                voc_dicts,
                voc_horizon,
                rules,
                weights,
                max_time_seconds,
                seed,
                verbose,
                should_stop,
            )
            voc_by_id = {s.id: s for s in vocational_sessions}
            voc_assignments = [
                a for a in voc_result.assignments if a.session_id in voc_by_id
            ]
            _persist_assignments(
                schedule,
                voc_by_id,
                voc_assignments,
                voc_horizon,
                lock=False,
            )
            tier_results.append(
                TierResult(
                    tier=VOCATIONAL,
                    status=voc_result.status,
                    objective_value=voc_result.objective_value,
                    assignments=voc_assignments,
                    violations=list(voc_result.violations),
                    num_sessions=len(vocational_sessions),
                    diagnostics=_tag(VOCATIONAL, voc_result.diagnostics),
                )
            )
            all_assignments.extend(voc_assignments)
            all_violations.extend(voc_result.violations)
            all_diagnostics.extend(_tag(VOCATIONAL, voc_result.diagnostics))
            objective_total += float(voc_result.objective_value or 0.0)
            if not voc_result.is_feasible:
                overall_status = Schedule.Status.FAILED
        else:
            horizon = _tenant_horizon(tenant, "horizon")
            all_sessions = _fetch_sessions(tenant)
            session_dicts = [_session_dict(s) for s in all_sessions]
            result = _solve_tier(
                tenant,
                session_dicts,
                horizon,
                rules,
                weights,
                max_time_seconds,
                seed,
                verbose,
                should_stop,
            )
            sessions_by_id = {s.id: s for s in all_sessions}
            _persist_assignments(
                schedule,
                sessions_by_id,
                result.assignments,
                horizon,
                lock=False,
            )
            tier_results.append(
                TierResult(
                    tier="all",
                    status=result.status,
                    objective_value=result.objective_value,
                    assignments=list(result.assignments),
                    violations=list(result.violations),
                    num_sessions=len(all_sessions),
                    diagnostics=_tag("all", result.diagnostics),
                )
            )
            all_assignments.extend(result.assignments)
            all_violations.extend(result.violations)
            all_diagnostics.extend(_tag("all", result.diagnostics))
            objective_total += float(result.objective_value or 0.0)
            if not result.is_feasible:
                overall_status = Schedule.Status.FAILED

        schedule.status = overall_status
        schedule.objective_value = objective_total
        schedule.save(update_fields=["status", "objective_value"])
    except Exception as exc:
        schedule.status = Schedule.Status.FAILED
        schedule.objective_value = None
        schedule.save(update_fields=["status", "objective_value"])
        all_violations.append("orchestrator error: %s" % exc)
        return OrchestratorResult(
            solve_job_id=solve_job_id,
            tier_mode=tier_mode,
            status=Schedule.Status.FAILED,
            objective_value=0.0,
            tier_results=tier_results,
            assignments=all_assignments,
            violations=all_violations,
            diagnostics=all_diagnostics,
        )

    return OrchestratorResult(
        solve_job_id=solve_job_id,
        tier_mode=tier_mode,
        status=overall_status,
        objective_value=objective_total,
        tier_results=tier_results,
        assignments=all_assignments,
        violations=all_violations,
        diagnostics=all_diagnostics,
    )
