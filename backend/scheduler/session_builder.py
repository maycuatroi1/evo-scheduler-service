"""Sinh buổi học từ số giờ chương trình.

Chương trình đào tạo khai theo *số giờ* cho mỗi mô-đun (lý thuyết bao
nhiêu, thực hành bao nhiêu), nhưng bộ giải xếp theo *buổi học*. Module này
bắc cầu giữa hai thứ đó.

Ba quy tắc rút từ thời khoá biểu trường đang phát hành:

1. **Buổi thực hành gộp dài.** Trên bản in, mô-đun thực hành thường chiếm
   trọn 3–5 tiết liền một buổi, không cắt rời từng tiết. Buổi lý thuyết
   ngắn hơn, phổ biến 2 tiết.

2. **Trần sĩ số nhân số buổi.** Nhóm 38 học sinh vào xưởng phải chia 3 ca
   vì trần thực hành là 18 (10 với nghề nặng nhọc, độc hại). Mỗi ca là một
   buổi riêng, cần một lượt xưởng và một lượt giáo viên.

3. **Buổi không được vắt qua ngày.** Buổi dài hơn số tiết một buổi học thì
   phải cắt thành nhiều buổi.
"""

from dataclasses import dataclass

from scheduler.models import Module, Session, StudentGroup

#: Trần sĩ số theo loại buổi, theo TT 07/2017/TT-BLĐTBXH.
CAP_THEORY = 35
CAP_PRACTICE = 18
CAP_PRACTICE_HAZARDOUS = 10

#: Độ dài buổi mặc định, tính bằng tiết.
THEORY_SLOTS = 2
PRACTICE_SLOTS = 3


@dataclass
class BuildPlan:
    """Kết quả dự tính, xem trước khi ghi vào cơ sở dữ liệu."""

    module_code: str
    group_code: str
    session_type: str
    tier: str
    slots_each: int
    count: int
    batches: int
    note: str = ""

    @property
    def total_periods(self):
        return self.slots_each * self.count


def batches_for(group, session_type, hazardous=None):
    """Số ca phải chia để không vượt trần sĩ số."""
    size = int(getattr(group, "size", 0) or 0)
    if size <= 0:
        return 1
    if session_type == Session.SessionType.PRACTICE:
        hz = getattr(group, "hazardous", False) if hazardous is None else hazardous
        cap = CAP_PRACTICE_HAZARDOUS if hz else CAP_PRACTICE
    else:
        cap = CAP_THEORY
    return max(1, -(-size // cap))


def _split(hours, slots_each, max_slots):
    """Chia tổng số giờ thành các buổi, buổi cuối nhận phần dư.

    Trả về danh sách độ dài từng buổi. Không buổi nào dài quá `max_slots`
    để tránh vắt qua ngày.
    """
    if hours <= 0:
        return []
    each = max(1, min(slots_each, max_slots))
    full, rest = divmod(hours, each)
    out = [each] * full
    if rest:
        out.append(rest)
    return out


def plan_for_module(module, group, max_slots_per_day, tier=None):
    """Dự tính các buổi cần sinh cho một mô-đun của một nhóm."""
    plans = []
    tier = tier or (
        Session.Tier.CULTURE
        if str(module.code).upper().startswith("VH")
        else Session.Tier.VOCATIONAL
    )

    for hours, stype, slots in (
        (int(module.theory_hours or 0), Session.SessionType.THEORY, THEORY_SLOTS),
        (int(module.practice_hours or 0), Session.SessionType.PRACTICE, PRACTICE_SLOTS),
    ):
        runs = _split(hours, slots, max_slots_per_day)
        if not runs:
            continue
        n_batches = batches_for(group, stype)
        # Gom các buổi cùng độ dài để bảng dự tính gọn
        by_len = {}
        for r in runs:
            by_len[r] = by_len.get(r, 0) + 1
        for slots_each, count in sorted(by_len.items(), reverse=True):
            note = ""
            if n_batches > 1:
                cap = (
                    CAP_PRACTICE_HAZARDOUS
                    if getattr(group, "hazardous", False)
                    else CAP_PRACTICE
                )
                note = "Nhóm %d học viên vượt trần %d nên chia %d ca" % (
                    group.size,
                    cap,
                    n_batches,
                )
            plans.append(
                BuildPlan(
                    module_code=module.code,
                    group_code=group.code,
                    session_type=stype,
                    tier=tier,
                    slots_each=slots_each,
                    count=count * n_batches,
                    batches=n_batches,
                    note=note,
                )
            )
    return plans


def plan(tenant, max_slots_per_day=5, module_codes=None, group_codes=None):
    """Dự tính toàn bộ buổi học cần sinh cho một đơn vị.

    Chỉ tính, không ghi. Gọi `apply` để ghi thật.
    """
    mods = Module.objects.filter(tenant=tenant)
    if module_codes:
        mods = mods.filter(code__in=module_codes)

    out = []
    for m in mods.select_related("student_group"):
        groups = []
        if m.student_group_id:
            groups = [m.student_group]
        else:
            qs = StudentGroup.objects.filter(tenant=tenant)
            if group_codes:
                qs = qs.filter(code__in=group_codes)
            groups = list(qs)
        for g in groups:
            if group_codes and g.code not in group_codes:
                continue
            out.extend(plan_for_module(m, g, max_slots_per_day))
    return out


def apply(tenant, schedule, max_slots_per_day=5, replace=True, **kw):
    """Sinh buổi học thật từ số giờ chương trình.

    `replace=True` xoá các buổi chưa khoá của lịch này trước khi sinh, để
    chạy lại nhiều lần không bị nhân đôi. Buổi đã khoá hoặc đã ghim luôn
    được giữ.
    """
    plans = plan(tenant, max_slots_per_day=max_slots_per_day, **kw)

    removed = 0
    if replace:
        qs = Session.objects.filter(
            tenant=tenant, schedule=schedule, is_locked=False, is_pinned=False
        )
        removed = qs.count()
        qs.delete()

    mods = {m.code: m for m in Module.objects.filter(tenant=tenant)}
    groups = {g.code: g for g in StudentGroup.objects.filter(tenant=tenant)}

    created = []
    for p in plans:
        m, g = mods.get(p.module_code), groups.get(p.group_code)
        if not m or not g:
            continue
        for _ in range(p.count):
            created.append(
                Session(
                    tenant=tenant,
                    schedule=schedule,
                    module=m,
                    student_group=g,
                    session_type=p.session_type,
                    tier=p.tier,
                    duration_slots=p.slots_each,
                )
            )
    Session.objects.bulk_create(created, batch_size=500)

    return {
        "created": len(created),
        "removed": removed,
        "total_periods": sum(p.total_periods for p in plans),
        "plans": len(plans),
    }
