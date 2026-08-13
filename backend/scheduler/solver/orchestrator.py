import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

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
]

DEFAULT_DAYS = [
    ("monday", 0),
    ("tuesday", 1),
    ("wednesday", 2),
    ("thursday", 3),
    ("friday", 4),
    ("saturday", 5),
]
DEFAULT_PERIODS_PER_DAY = 5
DEFAULT_MORNING_COUNT = 2


@dataclass
class TierResult:
    tier: str
    status: str
    objective_value: float
    assignments: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    num_sessions: int = 0


@dataclass
class OrchestratorResult:
    solve_job_id: str
    tier_mode: str
    status: str
    objective_value: float
    tier_results: list = field(default_factory=list)
    assignments: list = field(default_factory=list)
    violations: list = field(default_factory=list)


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


def _build_horizon(cfg) -> list:
    if not cfg:
        horizon = []
        idx = 0
        for name, d in DEFAULT_DAYS:
            for p in range(DEFAULT_PERIODS_PER_DAY):
                horizon.append(
                    {
                        "index": idx,
                        "week": 0,
                        "day": d,
                        "period": p,
                        "day_name": name,
                        "is_morning": p < DEFAULT_MORNING_COUNT,
                    }
                )
                idx += 1
        return horizon
    if isinstance(cfg, list):
        return _normalize_horizon(cfg)
    if isinstance(cfg, dict):
        if "weeks" in cfg or "days" in cfg or "periods_per_day" in cfg:
            weeks = int(cfg.get("weeks") or 1)
            days_cfg = cfg.get("days")
            periods = int(cfg.get("periods_per_day") or DEFAULT_PERIODS_PER_DAY)
            morning = int(cfg.get("morning_count") or DEFAULT_MORNING_COUNT)
            if days_cfg:
                day_names = []
                day_nums = []
                for i, d in enumerate(days_cfg):
                    if isinstance(d, dict):
                        nm = d.get("name", "day%d" % i)
                        dn = d.get("day", i)
                    else:
                        nm = d
                        dn = i
                    day_names.append(nm)
                    day_nums.append(dn)
            else:
                day_names = [n for n, _ in DEFAULT_DAYS]
                day_nums = [d for _, d in DEFAULT_DAYS]
            horizon = []
            idx = 0
            for w in range(weeks):
                for di, name in enumerate(day_names):
                    dnum = day_nums[di]
                    for p in range(periods):
                        horizon.append(
                            {
                                "index": idx,
                                "week": w,
                                "day": dnum,
                                "period": p,
                                "day_name": name,
                                "is_morning": p < morning,
                            }
                        )
                        idx += 1
            return horizon
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
    }


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


def _build_data(tenant, session_dicts, horizon, rules, weights) -> dict:
    return {
        "tenant_code": tenant.code,
        "horizon": horizon,
        "sessions": session_dicts,
        "resources": [_resource_to_dict(r) for r in tenant.resources.all()],
        "teachers": [_teacher_to_dict(t) for t in tenant.teachers.all()],
        "rules": list(rules),
        "hours_per_slot": 1.0,
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


def _solve_tier(
    tenant,
    session_dicts,
    horizon,
    rules,
    weights,
    max_time_seconds,
    seed,
    verbose,
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
    )


def orchestrate(
    schedule: Schedule,
    tenant: Any = None,
    data: Optional[dict] = None,
    max_time_seconds: float = DEFAULT_MAX_TIME_SECONDS,
    seed: int = DEFAULT_SEED,
    verbose: bool = False,
    weights: Optional[dict] = None,
) -> OrchestratorResult:
    tenant = tenant or schedule.tenant
    tier_mode = _tenant_tier_mode(tenant)
    solve_job_id = uuid.uuid4().hex

    if weights is None:
        weights = merge_weights(schedule.weights_json)
    rules = _rule_dicts_for(tenant) + CROSS_TIER_RULES

    schedule.status = Schedule.Status.SOLVING
    schedule.objective_value = None
    schedule.save(update_fields=["status", "objective_value"])

    tier_results: list = []
    all_assignments: list = []
    all_violations: list = []
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
                )
            )
            all_assignments.extend(culture_result.assignments)
            all_violations.extend(culture_result.violations)
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
                )
            )
            all_assignments.extend(voc_assignments)
            all_violations.extend(voc_result.violations)
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
                )
            )
            all_assignments.extend(result.assignments)
            all_violations.extend(result.violations)
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
        )

    return OrchestratorResult(
        solve_job_id=solve_job_id,
        tier_mode=tier_mode,
        status=overall_status,
        objective_value=objective_total,
        tier_results=tier_results,
        assignments=all_assignments,
        violations=all_violations,
    )
