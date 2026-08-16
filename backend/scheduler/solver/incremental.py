from dataclasses import dataclass, field
from typing import Any, Optional

from django.db import transaction
from ortools.sat.python import cp_model

from scheduler.solver.context import BuildContext
from scheduler.solver.constraints import apply_rule
from scheduler.solver import objectives
from scheduler.solver.objectives import merge_weights
from scheduler.solver.result import SolveResult, Assignment
from scheduler.solver.engine import _build_variables, _apply_locked, _resource_overlap
from scheduler.solver.orchestrator import (
    CROSS_TIER_RULES,
    _build_data,
    _rule_dicts_for,
    _session_dict,
    _tenant_horizon,
)

DEFAULT_INCREMENTAL_TIME_SECONDS = 5.0
DEFAULT_SEED = 42


class InfeasibleMove(Exception):
    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail or message


@dataclass
class IncrementalDiff:
    changed_sessions: list = field(default_factory=list)
    unchanged_sessions: list = field(default_factory=list)
    objective_value: float = 0.0
    status: str = ""
    wall_time: float = 0.0
    dragged_session_id: Optional[int] = None

    def to_dict(self):
        return {
            "changed_sessions": list(self.changed_sessions),
            "unchanged_session_ids": list(self.unchanged_sessions),
            "unchanged_count": len(self.unchanged_sessions),
            "objective_value": self.objective_value,
            "status": self.status,
            "wall_time": self.wall_time,
            "dragged_session_id": self.dragged_session_id,
        }


def _resolve_horizon_index(horizon, day, period):
    if day is None or period is None:
        return None
    for i, ts in enumerate(horizon):
        if ts.get("day") == day and ts.get("period") == period:
            return i
    return None


def _session_neighborhood(session_dicts, dragged_id):
    dragged = next((s for s in session_dicts if s["id"] == dragged_id), None)
    if not dragged:
        return set()
    teachers = set(dragged.get("teacher_codes") or [])
    group = dragged.get("group_code")
    resource = dragged.get("assigned_resource_code")
    out = set()
    for s in session_dicts:
        if s["id"] == dragged_id:
            continue
        s_teachers = set(s.get("teacher_codes") or [])
        if teachers and (teachers & s_teachers):
            out.add(s["id"])
            continue
        if group is not None and s.get("group_code") == group:
            out.add(s["id"])
            continue
        if resource is not None and s.get("assigned_resource_code") == resource:
            out.add(s["id"])
    return out


def _capture_old_assignments(sessions, horizon):
    out = {}
    for s in sessions:
        ats = getattr(s, "assigned_timeslot", None)
        if not ats:
            continue
        if isinstance(ats, dict):
            day = ats.get("day")
            period = ats.get("period")
        else:
            day = period = None
        idx = _resolve_horizon_index(horizon, day, period)
        res = getattr(getattr(s, "assigned_resource", None), "code", None)
        out[s.id] = {
            "timeslot_index": idx,
            "day": day,
            "period": period,
            "resource_code": res,
        }
    return out


def _solve_with_hints(data, max_time_seconds, weights, old_assignments):
    model = cp_model.CpModel()
    ctx = BuildContext(model, data)
    if not ctx.sessions:
        return SolveResult(status="UNKNOWN", objective_value=0.0, solver_log="no sessions")
    _build_variables(ctx)
    _apply_locked(ctx)
    _resource_overlap(ctx)

    objective_terms = []
    for rule in data.get("rules", []):
        if not rule.get("active", True):
            continue
        try:
            term = apply_rule(ctx, rule)
        except Exception:
            continue
        if term is not None:
            objective_terms.append(term)
    objective_terms = objectives.build_objective(ctx, weights, objective_terms)
    if objective_terms:
        model.Minimize(sum(objective_terms))

    for sid, info in old_assignments.items():
        t = info.get("timeslot_index")
        r = info.get("resource_code")
        if t is None or r is None:
            continue
        start_lit = ctx.start_lit.get((sid, t))
        if start_lit is not None:
            model.AddHint(start_lit, 1)
        res_lit = ctx.assign.get((sid, r))
        if res_lit is not None:
            model.AddHint(res_lit, 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(max_time_seconds)
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = DEFAULT_SEED
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    result = SolveResult(
        status=status_name,
        objective_value=float(solver.ObjectiveValue()) if status_name in ("OPTIMAL", "FEASIBLE") else 0.0,
        num_constraints=len(model.Proto().constraints),
        num_booleans=solver.NumBooleans(),
        wall_time=float(solver.WallTime()),
    )
    if status_name not in ("OPTIMAL", "FEASIBLE"):
        result.violations = ["model is %s" % status_name]
        return result

    for s in ctx.sessions:
        sid = s["id"]
        chosen_t, chosen_r = ctx.solution_for(solver, sid)
        if chosen_t is None:
            continue
        ts = ctx.horizon[chosen_t]
        result.assignments.append(Assignment(
            session_id=sid,
            session_code=s["code"],
            timeslot_index=chosen_t,
            day=ts["day"],
            period=ts["period"],
            day_name=ts.get("day_name", ""),
            resource_code=chosen_r,
            teacher_codes=list(s.get("teacher_codes", [])),
        ))
    return result


def incremental_resolve(
    schedule,
    session_id,
    new_day,
    new_period,
    new_resource_code=None,
    max_time_seconds=DEFAULT_INCREMENTAL_TIME_SECONDS,
    weights=None,
):
    from scheduler.models import Session

    tenant = schedule.tenant
    horizon = _tenant_horizon(tenant, "horizon")
    if not horizon:
        raise InfeasibleMove("horizon rong", "tenant chua cau hinh horizon")

    target_idx = _resolve_horizon_index(horizon, new_day, new_period)
    if target_idx is None:
        raise InfeasibleMove(
            "timeslot khong nam trong horizon",
            "day=%s period=%s" % (new_day, new_period),
        )

    try:
        dragged = tenant.sessions.get(id=session_id)
    except Session.DoesNotExist:
        raise InfeasibleMove("khong tim thay session", str(session_id))

    if getattr(dragged, "is_locked", False):
        raise InfeasibleMove("session bi khoa", str(session_id))

    all_sessions = list(
        tenant.sessions.select_related("module", "student_group", "assigned_resource")
        .prefetch_related("assigned_teachers")
    )
    session_dicts = [_session_dict(s) for s in all_sessions]

    dragged_dict = next((s for s in session_dicts if s["id"] == session_id), None)
    if dragged_dict is None:
        raise InfeasibleMove("session khong thuoc tenant", str(session_id))

    valid_resources = [r.code for r in tenant.resources.all()]
    if new_resource_code is None:
        new_resource_code = dragged_dict.get("assigned_resource_code")
    if new_resource_code is None:
        raise InfeasibleMove("thieu resource", "session chua co resource va body khong gui new_resource")
    if new_resource_code not in valid_resources:
        raise InfeasibleMove("resource khong kha dung", str(new_resource_code))

    target_ts = horizon[target_idx]
    dragged_dict["is_locked"] = True
    dragged_dict["assigned_timeslot"] = {
        "index": target_idx,
        "day": target_ts["day"],
        "period": target_ts["period"],
        "day_name": target_ts.get("day_name", ""),
    }
    dragged_dict["assigned_resource_code"] = new_resource_code

    neighborhood = _session_neighborhood(session_dicts, session_id)
    for s in session_dicts:
        if s["id"] in neighborhood:
            s["assigned_timeslot"] = None
            s["assigned_resource_code"] = None
            s["is_locked"] = False

    if weights is None:
        weights = merge_weights(schedule.weights_json)
    rules = _rule_dicts_for(tenant) + CROSS_TIER_RULES
    data = _build_data(tenant, session_dicts, horizon, rules, weights)

    old_assignments = _capture_old_assignments(all_sessions, horizon)
    hint_assignments = dict(old_assignments)
    hint_assignments[session_id] = {
        "timeslot_index": target_idx,
        "day": target_ts["day"],
        "period": target_ts["period"],
        "resource_code": new_resource_code,
    }

    result = _solve_with_hints(data, max_time_seconds, weights, hint_assignments)
    if not result.is_feasible:
        raise InfeasibleMove(
            "khong the sua lich trong gioi han thoi gian",
            "; ".join(result.violations[:3]) or result.status,
        )

    diff = _persist_and_diff(
        schedule,
        all_sessions,
        horizon,
        result,
        session_id,
        old_assignments,
    )
    diff.objective_value = result.objective_value
    diff.status = result.status
    diff.wall_time = result.wall_time
    diff.dragged_session_id = session_id
    return diff


def _persist_and_diff(schedule, sessions, horizon, result, dragged_id, old_assignments):
    sessions_by_id = {s.id: s for s in sessions}
    res_by_code = {r.code: r for r in schedule.tenant.resources.all()}
    new_map = {a.session_id: a for a in result.assignments}
    changed = []
    unchanged = []
    with transaction.atomic():
        for sid, sess in sessions_by_id.items():
            new_a = new_map.get(sid)
            old = old_assignments.get(sid, {
                "timeslot_index": None,
                "day": None,
                "period": None,
                "resource_code": None,
            })
            if new_a is None:
                unchanged.append(sid)
                continue
            new_t = new_a.timeslot_index
            new_r = new_a.resource_code
            moved = (
                old.get("timeslot_index") != new_t
                or old.get("resource_code") != new_r
            )
            if moved:
                ts = horizon[new_t]
                sess.assigned_timeslot = {
                    "index": new_t,
                    "day": new_a.day,
                    "period": new_a.period,
                    "day_name": new_a.day_name,
                    "week": ts.get("week", 0),
                }
                sess.assigned_resource = res_by_code.get(new_r)
                sess.save(update_fields=["assigned_timeslot", "assigned_resource"])
                changed.append({
                    "session_id": sid,
                    "old_day": old.get("day"),
                    "old_period": old.get("period"),
                    "old_resource": old.get("resource_code"),
                    "new_day": new_a.day,
                    "new_period": new_a.period,
                    "new_resource": new_r,
                    "is_dragged": sid == dragged_id,
                })
            else:
                unchanged.append(sid)
    return IncrementalDiff(changed_sessions=changed, unchanged_sessions=unchanged)
