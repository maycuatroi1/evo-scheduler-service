from scheduler.solver.context import BuildContext
from scheduler.solver.constraints._common import param


def apply(ctx: BuildContext, rule):
    rcode = param(rule, "entity_code", "resource_code", "entity", default=None)
    for s in ctx.sessions:
        group_size = int(s.get("group_size", 0) or 0)
        for r in ctx.resources:
            if rcode and r["code"] != rcode:
                continue
            capacity = int(r.get("capacity", 0) or 0)
            # Sức chứa 0 nghĩa là không khai báo giới hạn (bộ dụng cụ), loại
            # bỏ chúng sẽ khiến mọi buổi thực hành mất chỗ.
            if capacity == 0 or capacity >= group_size:
                continue
            lit = ctx.assign.get((s["id"], r["code"]))
            if lit is not None:
                ctx.model.Add(lit == 0)
    return None
