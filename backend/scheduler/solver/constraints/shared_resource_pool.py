from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    ctx.enforce_resource_capacity()
    return None
