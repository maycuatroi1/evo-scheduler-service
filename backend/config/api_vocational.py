"""API cho nghiệp vụ trường nghề.

Tách khỏi ``config.api`` để file gốc không phình thêm. Gồm CRUD dữ liệu
nền, ghim tiết, độ ưu tiên ràng buộc, kế thừa lịch cũ và xuất bản.
"""

from django.db import transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from scheduler.auth import tenant_auth
from scheduler.models import (
    Campus,
    ConstraintRule,
    Department,
    HomeroomClass,
    Module,
    Resource,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    User,
)

router = Router(auth=tenant_auth)


# --------------------------------------------------------------------------
# Phân quyền
# --------------------------------------------------------------------------

def _require(request, allowed):
    """Chặn thao tác nếu vai trò không nằm trong danh sách cho phép."""
    role = request.auth.get("role", "registrar")
    if role not in allowed:
        raise HttpError(
            403,
            "Vai trò %s không có quyền thực hiện thao tác này" % role,
        )
    return role


def _can_write(request):
    return _require(request, {"admin", "registrar"})


def _tenant(request):
    return request.auth["tenant"]


def _scoped(model, request):
    return model.objects.filter(tenant_id=request.auth["tenant_id"])


def _get_or_404(model, request, pk, label):
    try:
        obj = model.objects.get(id=pk)
    except (model.DoesNotExist, ValueError, TypeError):
        raise HttpError(404, "%s không tồn tại" % label)
    if obj.tenant_id != request.auth["tenant_id"]:
        raise HttpError(404, "%s không tồn tại" % label)
    return obj


# --------------------------------------------------------------------------
# Cơ sở đào tạo
# --------------------------------------------------------------------------

class CampusIn(Schema):
    code: str
    name: str
    address: str = ""
    travel_minutes: int = 0


class CampusOut(Schema):
    id: int
    code: str
    name: str
    address: str
    travel_minutes: int


@router.get("/campuses", response=list[CampusOut])
def list_campuses(request):
    return list(_scoped(Campus, request))


@router.post("/campuses", response={201: CampusOut})
def create_campus(request, payload: CampusIn):
    _can_write(request)
    if _scoped(Campus, request).filter(code=payload.code).exists():
        raise HttpError(400, "Mã cơ sở %s đã tồn tại" % payload.code)
    obj = Campus.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, obj


@router.put("/campuses/{campus_id}", response=CampusOut)
def update_campus(request, campus_id: int, payload: CampusIn):
    _can_write(request)
    obj = _get_or_404(Campus, request, campus_id, "Cơ sở")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return obj


@router.delete("/campuses/{campus_id}")
def delete_campus(request, campus_id: int):
    _can_write(request)
    _get_or_404(Campus, request, campus_id, "Cơ sở").delete()
    return {"deleted": True}


# --------------------------------------------------------------------------
# Khoa / tổ bộ môn
# --------------------------------------------------------------------------

class DepartmentIn(Schema):
    code: str
    name: str
    parent_id: int | None = None


class DepartmentOut(Schema):
    id: int
    code: str
    name: str
    parent_id: int | None = None


@router.get("/departments", response=list[DepartmentOut])
def list_departments(request):
    return list(_scoped(Department, request))


@router.post("/departments", response={201: DepartmentOut})
def create_department(request, payload: DepartmentIn):
    _can_write(request)
    if _scoped(Department, request).filter(code=payload.code).exists():
        raise HttpError(400, "Mã khoa %s đã tồn tại" % payload.code)
    obj = Department.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, obj


@router.put("/departments/{dept_id}", response=DepartmentOut)
def update_department(request, dept_id: int, payload: DepartmentIn):
    _can_write(request)
    obj = _get_or_404(Department, request, dept_id, "Khoa")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return obj


@router.delete("/departments/{dept_id}")
def delete_department(request, dept_id: int):
    _can_write(request)
    _get_or_404(Department, request, dept_id, "Khoa").delete()
    return {"deleted": True}


# --------------------------------------------------------------------------
# Lớp văn hoá
# --------------------------------------------------------------------------

class HomeroomIn(Schema):
    code: str
    name: str = ""
    grade: int | None = None
    size: int = 0
    culture_shift: str = "morning"
    room_id: int | None = None


class HomeroomOut(Schema):
    id: int
    code: str
    name: str
    grade: int | None = None
    size: int
    culture_shift: str
    vocational_shift: str
    room_id: int | None = None
    group_count: int = 0


def _homeroom_out(h):
    return {
        "id": h.id,
        "code": h.code,
        "name": h.name,
        "grade": h.grade,
        "size": h.size,
        "culture_shift": h.culture_shift,
        "vocational_shift": h.vocational_shift(),
        "room_id": h.room_id,
        "group_count": h.groups.count(),
    }


@router.get("/homerooms", response=list[HomeroomOut])
def list_homerooms(request, grade: int | None = None):
    qs = _scoped(HomeroomClass, request)
    if grade is not None:
        qs = qs.filter(grade=grade)
    return [_homeroom_out(h) for h in qs]


@router.post("/homerooms", response={201: HomeroomOut})
def create_homeroom(request, payload: HomeroomIn):
    _can_write(request)
    if _scoped(HomeroomClass, request).filter(code=payload.code).exists():
        raise HttpError(400, "Mã lớp %s đã tồn tại" % payload.code)
    obj = HomeroomClass.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, _homeroom_out(obj)


@router.put("/homerooms/{hid}", response=HomeroomOut)
def update_homeroom(request, hid: int, payload: HomeroomIn):
    _can_write(request)
    obj = _get_or_404(HomeroomClass, request, hid, "Lớp văn hoá")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return _homeroom_out(obj)


@router.delete("/homerooms/{hid}")
def delete_homeroom(request, hid: int):
    _can_write(request)
    _get_or_404(HomeroomClass, request, hid, "Lớp văn hoá").delete()
    return {"deleted": True}


# --------------------------------------------------------------------------
# Nhóm nghề và liên kết với lớp văn hoá
# --------------------------------------------------------------------------

class GroupIn(Schema):
    code: str
    name: str
    enrollment_type: str = "dual_degree"
    size: int = 0
    occupation: str = ""
    hazardous: bool = False
    homeroom_ids: list[int] = []


class GroupOut(Schema):
    id: int
    code: str
    name: str
    enrollment_type: str
    size: int
    occupation: str
    hazardous: bool
    homeroom_codes: list[str] = []
    practice_batches: int = 1


def _group_out(g):
    """Số ca thực hành suy từ trần sĩ số — đây là lý do trường tách nhóm."""
    cap = 10 if g.hazardous else 18
    batches = max(1, -(-g.size // cap)) if g.size else 1
    return {
        "id": g.id,
        "code": g.code,
        "name": g.name,
        "enrollment_type": g.enrollment_type,
        "size": g.size,
        "occupation": g.occupation,
        "hazardous": g.hazardous,
        "homeroom_codes": [h.code for h in g.homerooms.all()],
        "practice_batches": batches,
    }


@router.get("/groups", response=list[GroupOut])
def list_groups(request, homeroom: str | None = None):
    qs = _scoped(StudentGroup, request).prefetch_related("homerooms")
    if homeroom:
        qs = qs.filter(homerooms__code=homeroom)
    return [_group_out(g) for g in qs]


@router.post("/groups", response={201: GroupOut})
def create_group(request, payload: GroupIn):
    _can_write(request)
    data = payload.dict()
    homeroom_ids = data.pop("homeroom_ids", [])
    if _scoped(StudentGroup, request).filter(code=data["code"]).exists():
        raise HttpError(400, "Mã nhóm %s đã tồn tại" % data["code"])
    obj = StudentGroup.objects.create(tenant=_tenant(request), **data)
    if homeroom_ids:
        obj.homerooms.set(_scoped(HomeroomClass, request).filter(id__in=homeroom_ids))
    return 201, _group_out(obj)


@router.put("/groups/{gid}", response=GroupOut)
def update_group(request, gid: int, payload: GroupIn):
    _can_write(request)
    obj = _get_or_404(StudentGroup, request, gid, "Nhóm nghề")
    data = payload.dict()
    homeroom_ids = data.pop("homeroom_ids", None)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.save()
    if homeroom_ids is not None:
        obj.homerooms.set(_scoped(HomeroomClass, request).filter(id__in=homeroom_ids))
    return _group_out(obj)


@router.delete("/groups/{gid}")
def delete_group(request, gid: int):
    _can_write(request)
    _get_or_404(StudentGroup, request, gid, "Nhóm nghề").delete()
    return {"deleted": True}


@router.get("/homerooms/{hid}/split")
def homeroom_split(request, hid: int):
    """Lớp này tách thành mấy nhóm nghề, tổng bao nhiêu học sinh.

    Dùng cho cảnh báo trên giao diện: lớp tách nhiều nhóm thì các nhóm
    không được trùng giờ nhau.
    """
    h = _get_or_404(HomeroomClass, request, hid, "Lớp văn hoá")
    groups = list(h.groups.all())
    return {
        "homeroom": h.code,
        "declared_size": h.size,
        "group_count": len(groups),
        "total_in_groups": sum(g.size for g in groups),
        "is_split": len(groups) > 1,
        "groups": [
            {"code": g.code, "name": g.name, "size": g.size} for g in groups
        ],
    }


# --------------------------------------------------------------------------
# Phòng, xưởng, thiết bị
# --------------------------------------------------------------------------

class ResourceIn(Schema):
    code: str
    name: str
    type: str = "theory_room"
    capacity: int = 0
    quantity: int = 1
    available_quantity: int = 1


class ResourceOut(Schema):
    id: int
    code: str
    name: str
    type: str
    capacity: int
    quantity: int
    available_quantity: int


@router.get("/resources", response=list[ResourceOut])
def list_resources(request, type: str | None = None):
    qs = _scoped(Resource, request)
    if type:
        qs = qs.filter(type=type)
    return list(qs)


@router.post("/resources", response={201: ResourceOut})
def create_resource(request, payload: ResourceIn):
    _can_write(request)
    valid = {c[0] for c in Resource.ResourceType.choices}
    if payload.type not in valid:
        raise HttpError(400, "Loại phòng không hợp lệ: %s" % payload.type)
    if _scoped(Resource, request).filter(code=payload.code).exists():
        raise HttpError(400, "Mã phòng %s đã tồn tại" % payload.code)
    obj = Resource.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, obj


@router.put("/resources/{rid}", response=ResourceOut)
def update_resource(request, rid: int, payload: ResourceIn):
    _can_write(request)
    obj = _get_or_404(Resource, request, rid, "Phòng")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return obj


@router.delete("/resources/{rid}")
def delete_resource(request, rid: int):
    _can_write(request)
    _get_or_404(Resource, request, rid, "Phòng").delete()
    return {"deleted": True}


@router.get("/reports/room-usage")
def room_usage(request, schedule_id: int | None = None):
    """Suất sử dụng từng phòng: bao nhiêu tiết trên tổng số tiết khả dụng."""
    from scheduler import horizon as horizon_mod

    cfg = (_tenant(request).config_json or {}).get("horizon", {})
    slots = horizon_mod.total_slots(cfg) or 1

    qs = Session.objects.filter(tenant_id=request.auth["tenant_id"])
    if schedule_id is not None:
        qs = qs.filter(schedule_id=schedule_id)

    used = {}
    for s in qs.select_related("assigned_resource"):
        r = s.assigned_resource
        if r is None or not s.consumes_resources():
            continue
        used[r.code] = used.get(r.code, 0) + int(s.duration_slots or 1)

    rows = []
    for r in _scoped(Resource, request):
        cap_slots = slots * max(1, r.available_quantity or 1)
        periods = used.get(r.code, 0)
        rows.append(
            {
                "code": r.code,
                "name": r.name,
                "type": r.type,
                "capacity": r.capacity,
                "quantity": r.quantity,
                "periods_used": periods,
                "slots_available": cap_slots,
                "usage_pct": round(periods / cap_slots * 100, 1) if cap_slots else 0,
            }
        )
    rows.sort(key=lambda x: -x["usage_pct"])
    return {"rooms": rows, "total_slots_per_room": slots}


# --------------------------------------------------------------------------
# Giáo viên — hồ sơ đầy đủ
# --------------------------------------------------------------------------

class TeacherIn(Schema):
    code: str
    name: str
    blocks: list[str] = []
    quota_standard_hours: float | None = None
    moet_code: str = ""
    email: str = ""
    department_id: int | None = None
    campus_id: int | None = None
    max_periods_per_session: int | None = None
    min_periods_per_session: int | None = None
    days_off_per_week: int | None = None


class TeacherOut(Schema):
    id: int
    code: str
    name: str
    blocks: list[str] = []
    quota_standard_hours: float | None = None
    moet_code: str = ""
    email: str = ""
    department_id: int | None = None
    campus_id: int | None = None
    max_periods_per_session: int | None = None
    min_periods_per_session: int | None = None
    days_off_per_week: int | None = None


@router.get("/teachers/full", response=list[TeacherOut])
def list_teachers_full(request, department: int | None = None):
    qs = _scoped(Teacher, request)
    if department is not None:
        qs = qs.filter(department_id=department)
    return list(qs)


@router.post("/teachers", response={201: TeacherOut})
def create_teacher(request, payload: TeacherIn):
    _can_write(request)
    if _scoped(Teacher, request).filter(code=payload.code).exists():
        raise HttpError(400, "Mã giáo viên %s đã tồn tại" % payload.code)
    obj = Teacher.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, obj


@router.put("/teachers/{tid}", response=TeacherOut)
def update_teacher(request, tid: int, payload: TeacherIn):
    _can_write(request)
    obj = _get_or_404(Teacher, request, tid, "Giáo viên")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return obj


@router.delete("/teachers/{tid}")
def delete_teacher(request, tid: int):
    _can_write(request)
    _get_or_404(Teacher, request, tid, "Giáo viên").delete()
    return {"deleted": True}


@router.get("/reports/teacher-workload")
def teacher_workload(request):
    """Tải giảng dạy quy đổi giờ chuẩn, đối chiếu định mức từng người.

    Quy đổi theo TT 07/2017: 45 phút lý thuyết = 1 giờ chuẩn, 60 phút
    thực hành = 1 giờ chuẩn, nên tiết thực hành 45 phút chỉ bằng 0,75.
    Buổi thực tập và buổi ngoài trường không tính vào định mức.
    """
    rows = []
    for t in _scoped(Teacher, request).prefetch_related("sessions"):
        lt = th = 0
        for s in t.sessions.all():
            if not s.consumes_resources():
                continue
            slots = int(s.duration_slots or 1)
            if s.session_type == Session.SessionType.PRACTICE:
                th += slots
            else:
                lt += slots
        standard = round(lt * 1.0 + th * 0.75, 1)
        quota = t.quota_standard_hours or 550
        rows.append(
            {
                "code": t.code,
                "name": t.name,
                "department_id": t.department_id,
                "theory_periods": lt,
                "practice_periods": th,
                "standard_hours": standard,
                "quota": quota,
                "over": max(0, round(standard - quota, 1)),
                "usage_pct": round(standard / quota * 100, 1) if quota else 0,
            }
        )
    rows.sort(key=lambda r: -r["standard_hours"])
    return {"teachers": rows, "count": len(rows)}


# --------------------------------------------------------------------------
# Ghim tiết trước khi chạy bộ giải
# --------------------------------------------------------------------------

class PinIn(Schema):
    session_id: int
    day: int
    period: int
    week: int = 0


@router.get("/schedule/{schedule_id}/pins")
def list_pins(request, schedule_id: int):
    qs = Session.objects.filter(
        tenant_id=request.auth["tenant_id"], schedule_id=schedule_id, is_pinned=True
    )
    return {
        "schedule_id": schedule_id,
        "pins": [
            {
                "session_id": s.id,
                "module_code": s.module.code,
                "group_code": s.student_group.code if s.student_group else None,
                "timeslot": s.assigned_timeslot,
            }
            for s in qs.select_related("module", "student_group")
        ],
    }


@router.post("/schedule/{schedule_id}/pins")
def add_pin(request, schedule_id: int, payload: PinIn):
    """Ghim một buổi vào ô cố định. Bộ giải giữ nguyên và xếp phần còn lại."""
    _can_write(request)
    s = _get_or_404(Session, request, payload.session_id, "Buổi học")
    s.assigned_timeslot = {
        "day": payload.day,
        "period": payload.period,
        "week": payload.week,
        "index": None,
    }
    s.is_pinned = True
    s.is_locked = True
    s.save(update_fields=["assigned_timeslot", "is_pinned", "is_locked"])
    return {"pinned": True, "session_id": s.id}


@router.delete("/schedule/{schedule_id}/pins/{session_id}")
def remove_pin(request, schedule_id: int, session_id: int):
    _can_write(request)
    s = _get_or_404(Session, request, session_id, "Buổi học")
    s.is_pinned = False
    s.is_locked = False
    s.save(update_fields=["is_pinned", "is_locked"])
    return {"pinned": False, "session_id": s.id}


# --------------------------------------------------------------------------
# Ràng buộc: CRUD và độ ưu tiên
# --------------------------------------------------------------------------

class RuleIn(Schema):
    type: str
    scope_json: dict = {}
    params_json: dict = {}
    hardness: str = "hard"
    priority: str = "low"
    weight: int = 1
    active: bool = True


class RuleOut(Schema):
    id: int
    type: str
    scope_json: dict
    params_json: dict
    hardness: str
    priority: str
    weight: int
    active: bool
    effective_weight: int


def _rule_out(r):
    return {
        "id": r.id,
        "type": r.type,
        "scope_json": r.scope_json,
        "params_json": r.params_json,
        "hardness": r.hardness,
        "priority": r.priority,
        "weight": r.weight,
        "active": r.active,
        "effective_weight": r.effective_weight(),
    }


@router.get("/rules", response=list[RuleOut])
def list_rules(request, type: str | None = None):
    qs = _scoped(ConstraintRule, request)
    if type:
        qs = qs.filter(type=type)
    return [_rule_out(r) for r in qs]


@router.post("/rules", response={201: RuleOut})
def create_rule(request, payload: RuleIn):
    _can_write(request)
    valid = {c[0] for c in ConstraintRule.RuleType.choices}
    if payload.type not in valid:
        raise HttpError(400, "Loại ràng buộc không hợp lệ: %s" % payload.type)
    obj = ConstraintRule.objects.create(tenant=_tenant(request), **payload.dict())
    return 201, _rule_out(obj)


@router.put("/rules/{rid}", response=RuleOut)
def update_rule(request, rid: int, payload: RuleIn):
    _can_write(request)
    obj = _get_or_404(ConstraintRule, request, rid, "Ràng buộc")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    obj.save()
    return _rule_out(obj)


@router.delete("/rules/{rid}")
def delete_rule(request, rid: int):
    _can_write(request)
    _get_or_404(ConstraintRule, request, rid, "Ràng buộc").delete()
    return {"deleted": True}


class PriorityIn(Schema):
    priority: str
    weight: int | None = None


@router.put("/rules/{rid}/priority", response=RuleOut)
def set_priority(request, rid: int, payload: PriorityIn):
    """Đặt độ ưu tiên: cao = giữ bằng mọi giá, thấp = bỏ được khi bí."""
    _can_write(request)
    valid = {c[0] for c in ConstraintRule.Priority.choices}
    if payload.priority not in valid:
        raise HttpError(400, "Độ ưu tiên không hợp lệ: %s" % payload.priority)
    obj = _get_or_404(ConstraintRule, request, rid, "Ràng buộc")
    obj.priority = payload.priority
    if payload.weight is not None:
        obj.weight = max(1, min(10, int(payload.weight)))
    obj.save(update_fields=["priority", "weight"])
    return _rule_out(obj)


# --------------------------------------------------------------------------
# Kế thừa lịch cũ
# --------------------------------------------------------------------------

@router.get("/schedule/{schedule_id}/inherit-diff")
def inherit_diff(request, schedule_id: int, base_id: int):
    """Dò giáo viên nào đổi phân công so với phiên bản gốc.

    Chỉ những người này cần xếp lại; phần còn lại giữ nguyên vị trí tiết.
    """
    target = _get_or_404(Schedule, request, schedule_id, "Lịch")
    base = _get_or_404(Schedule, request, base_id, "Lịch gốc")

    def load(sched):
        out = {}
        qs = Session.objects.filter(
            tenant_id=request.auth["tenant_id"], schedule=sched
        ).prefetch_related("assigned_teachers", "module")
        for s in qs:
            for t in s.assigned_teachers.all():
                out.setdefault(t.code, {"name": t.name, "modules": set()})
                out[t.code]["modules"].add(s.module.code)
        return out

    old, new = load(base), load(target)
    changed, unchanged = [], []
    for code in sorted(set(old) | set(new)):
        o = old.get(code, {"name": "", "modules": set()})
        n = new.get(code, {"name": "", "modules": set()})
        name = n["name"] or o["name"]
        added = sorted(n["modules"] - o["modules"])
        removed = sorted(o["modules"] - n["modules"])
        row = {
            "teacher_code": code,
            "teacher_name": name,
            "added_modules": added,
            "removed_modules": removed,
            "old_count": len(o["modules"]),
            "new_count": len(n["modules"]),
        }
        (changed if (added or removed) else unchanged).append(row)

    total = len(changed) + len(unchanged)
    return {
        "schedule_id": target.id,
        "base_id": base.id,
        "changed": changed,
        "unchanged_count": len(unchanged),
        "total_teachers": total,
        "keep_pct": round(len(unchanged) / total * 100, 1) if total else 100.0,
    }


class InheritIn(Schema):
    base_id: int
    keep_level: str = "max"


@router.post("/schedule/{schedule_id}/inherit")
def inherit_schedule(request, schedule_id: int, payload: InheritIn):
    """Sao chép vị trí tiết từ phiên bản gốc, khoá lại phần không đổi."""
    _can_write(request)
    target = _get_or_404(Schedule, request, schedule_id, "Lịch")
    base = _get_or_404(Schedule, request, payload.base_id, "Lịch gốc")

    diff = inherit_diff(request, schedule_id, payload.base_id)
    changed_codes = {r["teacher_code"] for r in diff["changed"]}

    # Bản đồ vị trí cũ theo (mã mô-đun, mã nhóm)
    old_pos = {}
    for s in Session.objects.filter(
        tenant_id=request.auth["tenant_id"], schedule=base
    ).select_related("module", "student_group"):
        if not s.assigned_timeslot:
            continue
        key = (s.module.code, s.student_group.code if s.student_group else None)
        old_pos[key] = (s.assigned_timeslot, s.assigned_resource_id)

    copied = skipped = 0
    with transaction.atomic():
        qs = Session.objects.filter(
            tenant_id=request.auth["tenant_id"], schedule=target
        ).select_related("module", "student_group").prefetch_related("assigned_teachers")
        for s in qs:
            codes = {t.code for t in s.assigned_teachers.all()}
            if codes & changed_codes:
                skipped += 1
                continue
            key = (s.module.code, s.student_group.code if s.student_group else None)
            if key not in old_pos:
                skipped += 1
                continue
            ts, res_id = old_pos[key]
            s.assigned_timeslot = ts
            s.assigned_resource_id = res_id
            s.is_locked = payload.keep_level == "max"
            s.save(
                update_fields=[
                    "assigned_timeslot",
                    "assigned_resource",
                    "is_locked",
                ]
            )
            copied += 1
        target.inherited_from = base
        target.save(update_fields=["inherited_from"])

    return {
        "schedule_id": target.id,
        "base_id": base.id,
        "copied": copied,
        "to_resolve": skipped,
        "changed_teachers": sorted(changed_codes),
        "keep_level": payload.keep_level,
    }


# --------------------------------------------------------------------------
# Xuất bản
# --------------------------------------------------------------------------

@router.post("/schedule/{schedule_id}/publish")
def publish_schedule(request, schedule_id: int):
    """Chốt phiên bản chính thức để phát hành tới giáo viên và sinh viên."""
    _require(request, {"admin", "registrar"})
    sched = _get_or_404(Schedule, request, schedule_id, "Lịch")
    if sched.status not in (Schedule.Status.SOLVED, Schedule.Status.PUBLISHED):
        raise HttpError(
            400,
            "Chỉ xuất bản được lịch đã giải xong; trạng thái hiện tại: %s"
            % sched.status,
        )
    unplaced = Session.objects.filter(
        tenant_id=request.auth["tenant_id"],
        schedule=sched,
        assigned_timeslot__isnull=True,
    ).count()

    user = None
    email = request.auth.get("email")
    if email:
        user = User.objects.filter(
            tenant_id=request.auth["tenant_id"], email=email
        ).first()

    sched.status = Schedule.Status.PUBLISHED
    sched.published_at = timezone.now()
    sched.published_by = user
    sched.unplaced_count = unplaced
    sched.save(
        update_fields=["status", "published_at", "published_by", "unplaced_count"]
    )
    return {
        "schedule_id": sched.id,
        "status": sched.status,
        "published_at": sched.published_at.isoformat(),
        "unplaced_count": unplaced,
    }


@router.get("/schedule/versions")
def list_versions(request):
    """Lịch sử phiên bản: bản gốc, bản đã tinh chỉnh, kế thừa từ đâu."""
    rows = []
    for s in _scoped(Schedule, request).select_related("inherited_from"):
        rows.append(
            {
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "is_manual_edit": s.is_manual_edit,
                "inherited_from": s.inherited_from_id,
                "week_number": s.week_number,
                "objective_value": s.objective_value,
                "unplaced_count": s.unplaced_count,
                "published_at": s.published_at.isoformat() if s.published_at else None,
            }
        )
    return {"versions": rows, "count": len(rows)}


# --------------------------------------------------------------------------
# Mốc giờ tiết học
# --------------------------------------------------------------------------

class BellIn(Schema):
    morning_start: str = "07:00"
    afternoon_start: str = "13:00"
    period_minutes: int = 45
    break_minutes: int = 5
    long_break_after: int = 2
    long_break_minutes: int = 15
    periods_per_shift: int = 5


def _bell_times(cfg):
    def to_min(t):
        try:
            h, m = str(t).split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return None

    def hhmm(m):
        return "%02d:%02d" % (m // 60, m % 60)

    out = {}
    for key, start in (
        ("morning", cfg.get("morning_start", "07:00")),
        ("afternoon", cfg.get("afternoon_start", "13:00")),
    ):
        t = to_min(start)
        if t is None:
            t = 7 * 60 if key == "morning" else 13 * 60
        rows = []
        n = int(cfg.get("periods_per_shift", 5) or 5)
        length = int(cfg.get("period_minutes", 45) or 45)
        brk = int(cfg.get("break_minutes", 5) or 5)
        after = int(cfg.get("long_break_after", 2) or 0)
        long_brk = int(cfg.get("long_break_minutes", 15) or 0)
        for p in range(1, n + 1):
            rows.append({"period": p, "start": hhmm(t), "end": hhmm(t + length)})
            t += length + brk + (long_brk if p == after else 0)
        out[key] = rows
    return out


@router.get("/tenant/bell-times")
def get_bell_times(request):
    cfg = (_tenant(request).config_json or {}).get("bell_times", {})
    return {"config": cfg or BellIn().dict(), "periods": _bell_times(cfg)}


@router.put("/tenant/bell-times")
def set_bell_times(request, payload: BellIn):
    _can_write(request)
    tenant = _tenant(request)
    cfg = dict(tenant.config_json or {})
    cfg["bell_times"] = payload.dict()
    tenant.config_json = cfg
    tenant.save(update_fields=["config_json"])
    return {"config": payload.dict(), "periods": _bell_times(payload.dict())}
