from scheduler.solver.constraints import (
    unavailability,
    resource_requirement,
    capacity_limit,
    quota_limit,
    preference,
    exclusion,
    adjacency,
    distribution,
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
}

__all__ = ["RULE_MODULES", "apply_rule"]


def apply_rule(ctx, rule):
    rtype = rule.get("type")
    mod = RULE_MODULES.get(rtype)
    if mod is None:
        return None
    return mod.apply(ctx, rule)
