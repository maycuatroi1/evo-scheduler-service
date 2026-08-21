from scheduler.solver.constraints import (
    unavailability,
    resource_requirement,
    capacity_limit,
    quota_limit,
    preference,
    exclusion,
    adjacency,
    distribution,
    teacher_no_overlap,
    student_no_overlap,
    shared_resource_pool,
    group_same_class,
    shift_by_grade,
    capacity_by_type,
    offsite_no_room,
)

RULE_MODULES = {
    "unavailability": unavailability,
    "resource_requirement": resource_requirement,
    "capacity_limit": capacity_limit,
    "quota_limit": quota_limit,
    "preference": preference,
    "exclusion": exclusion,
    "adjacency": adjacency,
    "distribution": distribution,
    "teacher_no_overlap": teacher_no_overlap,
    "student_no_overlap": student_no_overlap,
    "shared_resource_pool": shared_resource_pool,
    "group_same_class": group_same_class,
    "shift_by_grade": shift_by_grade,
    "capacity_by_type": capacity_by_type,
    "offsite_no_room": offsite_no_room,
}

__all__ = ["RULE_MODULES", "apply_rule"]


def apply_rule(ctx, rule):
    rtype = rule.get("type")
    mod = RULE_MODULES.get(rtype)
    if mod is None:
        return None
    return mod.apply(ctx, rule)
