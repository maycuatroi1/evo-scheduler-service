"""API cho nghiệp vụ trường nghề.

Tách khỏi ``config.api`` để file gốc không phình thêm. Gồm CRUD dữ liệu
nền, ghim tiết, độ ưu tiên ràng buộc, kế thừa lịch cũ và xuất bản.
"""

from django.db import transaction
from django.db.models import Q
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
# Sinh buổi học từ số giờ chương trình
# --------------------------------------------------------------------------

class BuildIn(Schema):
    max_slots_per_day: int = 5
    replace: bool = True
    module_codes: list[str] | None = None
    group_codes: list[str] | None = None


@router.get("/schedule/{schedule_id}/build-preview")
def build_preview(request, schedule_id: int, max_slots_per_day: int = 5):
    """Xem trước sẽ sinh ra bao nhiêu buổi, trước khi ghi thật."""
    from scheduler import session_builder

    _get_or_404(Schedule, request, schedule_id, "Lịch")
    plans = session_builder.plan(
        _tenant(request), max_slots_per_day=max_slots_per_day
    )
    return {
        "schedule_id": schedule_id,
        "plans": [
            {
                "module_code": p.module_code,
                "group_code": p.group_code,
                "session_type": p.session_type,
                "tier": p.tier,
                "slots_each": p.slots_each,
                "count": p.count,
                "batches": p.batches,
                "total_periods": p.total_periods,
                "note": p.note,
            }
            for p in plans
        ],
        "total_sessions": sum(p.count for p in plans),
        "total_periods": sum(p.total_periods for p in plans),
    }


@router.post("/schedule/{schedule_id}/build-sessions")
def build_sessions(request, schedule_id: int, payload: BuildIn):
    """Bung số giờ chương trình thành buổi học cụ thể.

    Buổi đã khoá hoặc đã ghim luôn được giữ, nên chạy lại nhiều lần không
    làm mất công tinh chỉnh.
    """
    _can_write(request)
    from scheduler import session_builder

    sched = _get_or_404(Schedule, request, schedule_id, "Lịch")
    with transaction.atomic():
        result = session_builder.apply(
            _tenant(request),
            sched,
            max_slots_per_day=payload.max_slots_per_day,
            replace=payload.replace,
            module_codes=payload.module_codes,
            group_codes=payload.group_codes,
        )
    result["schedule_id"] = sched.id
    return result


# --------------------------------------------------------------------------
# Mô-đun / môn học
# --------------------------------------------------------------------------

class ModuleIn(Schema):
    code: str
    name: str
    theory_hours: int = 0
    practice_hours: int = 0
    student_group_id: int | None = None


class ModuleOut(Schema):
    id: int
    code: str
    name: str
    theory_hours: int
    practice_hours: int
    student_group_id: int | None = None
    group_code: str = ""
    total_hours: int = 0
    session_count: int = 0


def _module_out(m, session_count=None):
    return {
        "id": m.id,
        "code": m.code,
        "name": m.name,
        "theory_hours": m.theory_hours,
        "practice_hours": m.practice_hours,
        "student_group_id": m.student_group_id,
        "group_code": m.student_group.code if m.student_group else "",
        "total_hours": m.theory_hours + m.practice_hours,
        "session_count": (
            m.sessions.count() if session_count is None else session_count
        ),
    }


@router.get("/modules", response=list[ModuleOut])
def list_modules(request, group: str | None = None, q: str | None = None):
    qs = _scoped(Module, request).select_related("student_group")
    if group:
        qs = qs.filter(student_group__code=group)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
    return [_module_out(m) for m in qs]


@router.post("/modules", response={201: ModuleOut})
def create_module(request, payload: ModuleIn):
    _can_write(request)
    data = payload.dict()
    if _scoped(Module, request).filter(code=data["code"]).exists():
        raise HttpError(400, "Mã mô-đun %s đã tồn tại" % data["code"])
    gid = data.pop("student_group_id", None)
    group = (
        _get_or_404(StudentGroup, request, gid, "Nhóm nghề") if gid else None
    )
    obj = Module.objects.create(
        tenant=_tenant(request), student_group=group, **data
    )
    return 201, _module_out(obj)


@router.put("/modules/{mid}", response=ModuleOut)
def update_module(request, mid: int, payload: ModuleIn):
    _can_write(request)
    obj = _get_or_404(Module, request, mid, "Mô-đun")
    data = payload.dict()
    gid = data.pop("student_group_id", None)
    obj.student_group = (
        _get_or_404(StudentGroup, request, gid, "Nhóm nghề") if gid else None
    )
    for k, v in data.items():
        setattr(obj, k, v)
    obj.save()
    return _module_out(obj)


@router.delete("/modules/{mid}")
def delete_module(request, mid: int):
    """Xoá mô-đun; từ chối nếu còn buổi học tham chiếu tới nó."""
    _can_write(request)
    obj = _get_or_404(Module, request, mid, "Mô-đun")
    used = obj.sessions.count()
    if used:
        raise HttpError(
            400,
            "Mô-đun %s còn %d buổi học đang dùng; xoá buổi trước."
            % (obj.code, used),
        )
    obj.delete()
    return {"deleted": True}


# --------------------------------------------------------------------------
# Chương trình đào tạo
# --------------------------------------------------------------------------

# Ngưỡng tỉ lệ thực hành theo TT 01/2024. Thông tư đang trong diện ban hành
# lại nên để ở cấu hình đơn vị, không mã hoá cứng (SRS §2.5).
DEFAULT_PRACTICE_RATIO = {
    "college": {"min": 50, "max": 70},
    "intermediate": {"min": 55, "max": 75},
    "dual_degree": {"min": 55, "max": 75},
}

PROGRAM_LABEL = {
    "college": "Cao đẳng",
    "intermediate": "Trung cấp",
    "dual_degree": "Trung cấp song bằng",
}


@router.get("/reports/programs")
def program_report(request):
    """Tổng hợp theo chương trình đào tạo: quỹ giờ và tỉ lệ LT/TH (FR-9.6).

    Đối chiếu tỉ lệ thực hành với ngưỡng quy định để cán bộ đào tạo biết
    chương trình nào đang lệch chuẩn.
    """
    cfg = (_tenant(request).config_json or {}).get("practice_ratio") or {}
    thresholds = {**DEFAULT_PRACTICE_RATIO}
    for key, val in cfg.items():
        if key in thresholds and isinstance(val, dict):
            thresholds[key] = {**thresholds[key], **val}

    buckets = {}
    groups = _scoped(StudentGroup, request).prefetch_related("modules")
    for g in groups:
        b = buckets.setdefault(
            g.enrollment_type,
            {
                "program": g.enrollment_type,
                "label": PROGRAM_LABEL.get(g.enrollment_type, g.enrollment_type),
                "group_count": 0,
                "student_count": 0,
                "module_count": 0,
                "theory_hours": 0,
                "practice_hours": 0,
            },
        )
        b["group_count"] += 1
        b["student_count"] += g.size or 0
        for m in g.modules.all():
            b["module_count"] += 1
            b["theory_hours"] += m.theory_hours or 0
            b["practice_hours"] += m.practice_hours or 0

    rows = []
    for b in buckets.values():
        total = b["theory_hours"] + b["practice_hours"]
        pct = round(b["practice_hours"] / total * 100, 1) if total else 0.0
        th = thresholds.get(b["program"], {})
        lo, hi = th.get("min"), th.get("max")
        if not total:
            trang_thai = "chua_khai_gio"
        elif lo is not None and pct < lo:
            trang_thai = "thieu_thuc_hanh"
        elif hi is not None and pct > hi:
            trang_thai = "thua_thuc_hanh"
        else:
            trang_thai = "dat"
        rows.append(
            {
                **b,
                "total_hours": total,
                "practice_pct": pct,
                "min_pct": lo,
                "max_pct": hi,
                "status": trang_thai,
            }
        )
    # Trung cấp đứng trước song bằng, đúng trình tự xếp lịch của trường.
    order = ["college", "intermediate", "dual_degree"]
    rows.sort(key=lambda r: order.index(r["program"]) if r["program"] in order else 99)
    return {"programs": rows, "count": len(rows)}


# --------------------------------------------------------------------------
# Cổng xem lịch cho giáo viên và sinh viên (FR-8.4)
# --------------------------------------------------------------------------

def _current_user(request):
    """Tài khoản đang đăng nhập, lấy từ claim user_id trong token."""
    uid = (request.auth.get("claims") or {}).get("user_id")
    if not uid:
        return None
    return (
        User.objects.select_related("teacher")
        .filter(id=uid, tenant_id=request.auth["tenant_id"])
        .first()
    )


def _session_rows(sessions, morning_count):
    rows = []
    for s in sessions:
        ts = s.assigned_timeslot or {}
        day, period = ts.get("day"), ts.get("period")
        if day is None or period is None:
            continue
        rows.append(
            {
                "session_id": s.id,
                "day": int(day),
                "period": int(period),
                "duration_slots": int(s.duration_slots or 1),
                "shift": (
                    "morning" if int(period) < morning_count else "afternoon"
                ),
                "module_code": s.module.code,
                "module_name": s.module.name,
                "group_code": s.student_group.code,
                "group_name": s.student_group.name,
                "room": s.assigned_resource.code if s.assigned_resource else "",
                "session_type": s.session_type,
                "teachers": [t.name for t in s.assigned_teachers.all()],
                "location": s.location,
            }
        )
    rows.sort(key=lambda r: (r["day"], r["period"]))
    return rows


@router.get("/me/schedule")
def my_schedule(request, schedule_id: int | None = None):
    """Lịch cá nhân của người đang đăng nhập.

    Giáo viên thấy các buổi mình dạy; sinh viên thấy lịch của nhóm mình.
    Chỉ trả lịch đã xuất bản, trừ khi người dùng có quyền sửa — cán bộ
    đào tạo cần xem trước bản nháp, còn giáo viên thì không, để tránh
    dạy theo một bản lịch chưa chốt.
    """
    from scheduler import horizon as horizon_mod

    user = _current_user(request)
    if user is None:
        raise HttpError(404, "Không tìm thấy tài khoản")

    tenant = _tenant(request)
    cfg = horizon_mod.normalize((tenant.config_json or {}).get("horizon"))
    morning_count = cfg["morning_count"]

    schedules = _scoped(Schedule, request)
    if not user.can_write():
        schedules = schedules.filter(status=Schedule.Status.PUBLISHED)
    if schedule_id is not None:
        schedules = schedules.filter(id=schedule_id)
    schedule = schedules.order_by("-published_at", "-id").first()

    base = {
        "role": user.role,
        "name": user.name,
        "schedule_id": schedule.id if schedule else None,
        "schedule_name": schedule.name if schedule else "",
        "published": bool(schedule and schedule.status == Schedule.Status.PUBLISHED),
        "morning_count": morning_count,
    }

    if schedule is None:
        return {**base, "sessions": [], "detail": "Chưa có lịch nào được xuất bản"}

    qs = (
        tenant.sessions.filter(schedule=schedule)
        .select_related("module", "student_group", "assigned_resource")
        .prefetch_related("assigned_teachers")
    )

    if user.role == User.Role.TEACHER:
        if user.teacher_id is None:
            return {
                **base,
                "sessions": [],
                "detail": "Tài khoản chưa gắn với hồ sơ giáo viên nào",
            }
        qs = qs.filter(assigned_teachers=user.teacher_id)
        base["teacher_code"] = user.teacher.code
    elif user.role == User.Role.STUDENT:
        # Chưa có liên kết tài khoản sinh viên với nhóm nghề, nên yêu cầu
        # chỉ rõ nhóm cần xem thay vì trả nhầm lịch của cả trường.
        group = request.GET.get("group")
        if not group:
            return {
                **base,
                "sessions": [],
                "detail": "Cần chọn nhóm nghề để xem lịch",
            }
        qs = qs.filter(student_group__code=group)
        base["group_code"] = group

    return {**base, "sessions": _session_rows(qs, morning_count)}


@router.get("/me/workload")
def my_workload(request):
    """Tải giảng dạy của chính giáo viên đang đăng nhập."""
    user = _current_user(request)
    if user is None:
        raise HttpError(404, "Không tìm thấy tài khoản")
    if user.teacher_id is None:
        raise HttpError(400, "Tài khoản chưa gắn với hồ sơ giáo viên nào")

    lt = th = 0
    for s in user.teacher.sessions.all():
        if not s.consumes_resources():
            continue
        slots = int(s.duration_slots or 1)
        if s.session_type == Session.SessionType.PRACTICE:
            th += slots
        else:
            lt += slots
    standard = round(lt * 1.0 + th * 0.75, 1)
    quota = user.teacher.quota_standard_hours or 550
    return {
        "code": user.teacher.code,
        "name": user.teacher.name,
        "theory_periods": lt,
        "practice_periods": th,
        "standard_hours": standard,
        "quota": quota,
        "usage_pct": round(standard / quota * 100, 1) if quota else 0,
    }


# --------------------------------------------------------------------------
# Tinh chỉnh thủ công: gợi ý ô đổi được (FR-7.8, FR-7.12)
# --------------------------------------------------------------------------

#: Bảng màu bắt buộc khi tinh chỉnh (SRS §7.5).
#: xanh = đổi tốt; hồng nhạt = vi phạm ràng buộc mềm; hồng đậm = trùng
#: tiết, chặn hẳn; da cam = vi phạm hạn chế xếp của giáo viên.
VERDICT_GREEN = "green"
VERDICT_PINK = "pink"
VERDICT_PINK_DARK = "pink_dark"
VERDICT_ORANGE = "orange"


def _span(session):
    """Buổi này chiếm ngày nào, từ tiết nào, dài mấy tiết."""
    ts = session.assigned_timeslot or {}
    day, period = ts.get("day"), ts.get("period")
    if day is None or period is None:
        return None
    return int(day), int(period), max(1, int(session.duration_slots or 1))


def _busy_map(sessions, skip_ids):
    """Ai bận tiết nào: (day, period) -> {teachers, rooms, groups}.

    Trải buổi ra đủ số tiết nó chiếm, nếu không sẽ bỏ sót chồng lấn của
    buổi thực hành dài (cùng lỗi với FR-7.11).
    """
    busy = {}
    for s in sessions:
        if s.id in skip_ids:
            continue
        sp = _span(s)
        if sp is None:
            continue
        day, period, n = sp
        for k in range(n):
            slot = busy.setdefault(
                (day, period + k),
                {"teachers": set(), "rooms": set(), "groups": set()},
            )
            slot["teachers"].update(t.id for t in s.assigned_teachers.all())
            if s.assigned_resource_id:
                slot["rooms"].add(s.assigned_resource_id)
            slot["groups"].add(s.student_group_id)
    return busy


def _days_in_use(sessions, teacher_ids):
    """Những ngày giáo viên đã có tiết — dùng để đếm ngày nghỉ còn lại."""
    days = set()
    for s in sessions:
        sp = _span(s)
        if sp is None:
            continue
        if teacher_ids & {t.id for t in s.assigned_teachers.all()}:
            days.add(sp[0])
    return days


def _judge(session, day, period, busy, day_budget=None, other=None):
    """Chấm một ô đích cho buổi ``session``; trả (màu, lý do)."""
    n = max(1, int(session.duration_slots or 1))
    tids = {t.id for t in session.assigned_teachers.all()}
    rid = session.assigned_resource_id
    gid = session.student_group_id

    trung = []
    for k in range(n):
        slot = busy.get((day, period + k))
        if not slot:
            continue
        if tids & slot["teachers"]:
            trung.append("giáo viên bận")
        if rid is not None and rid in slot["rooms"]:
            trung.append("phòng đã có lớp")
        if gid in slot["groups"]:
            trung.append("nhóm đang học môn khác")
    if trung:
        # Trùng tiết là chặn hẳn, không cho đổi.
        return VERDICT_PINK_DARK, "; ".join(sorted(set(trung)))

    # Đẩy giáo viên sang một ngày mới sẽ ăn mất ngày nghỉ đã khai.
    if day_budget is not None:
        used, allowed = day_budget
        if day not in used and len(used) + 1 > allowed:
            return (
                VERDICT_ORANGE,
                "chiếm mất ngày nghỉ trong tuần của giáo viên",
            )

    # Đổi hai buổi khác độ dài thì lưới lệch, phải xếp lại quanh đó.
    if other is not None and int(other.duration_slots or 1) != n:
        return VERDICT_PINK, "hai buổi khác số tiết nên phải xếp lại lưới"

    return VERDICT_GREEN, "đổi được"


def _day_budget(tenant, sessions, teacher_ids):
    """Số ngày giáo viên được phép có tiết, suy từ ``days_off_per_week``."""
    if not teacher_ids:
        return None
    nghi = [
        t.days_off_per_week
        for t in Teacher.objects.filter(id__in=teacher_ids)
        if t.days_off_per_week
    ]
    if not nghi:
        return None
    from scheduler import horizon as horizon_mod

    cfg = horizon_mod.normalize((tenant.config_json or {}).get("horizon"))
    allowed = max(1, len(cfg["days"]) - max(nghi))
    return _days_in_use(sessions, teacher_ids), allowed


@router.get("/schedule/{schedule_id}/swap-candidates/{session_id}")
def swap_candidates(request, schedule_id: int, session_id: int, scope: str = "group"):
    """Ô nào đổi được với buổi này, kèm màu theo bảng màu bắt buộc.

    ``scope="group"`` chỉ xét buổi cùng nhóm nghề — cách 1, đổi trực tiếp.
    ``scope="all"`` tô sáng mọi phân công toàn trường — cách 3.
    """
    schedule = _get_or_404(Schedule, request, schedule_id, "Lịch")
    tenant = _tenant(request)
    target = (
        tenant.sessions.select_related("student_group", "module")
        .prefetch_related("assigned_teachers")
        .filter(id=session_id, schedule=schedule)
        .first()
    )
    if target is None:
        raise HttpError(404, "Buổi học không tồn tại")
    if target.is_locked or target.is_pinned:
        raise HttpError(400, "Buổi đã khoá hoặc đã ghim nên không đổi được")

    everything = list(
        tenant.sessions.filter(schedule=schedule)
        .select_related("student_group", "module", "assigned_resource")
        .prefetch_related("assigned_teachers")
    )
    others = [s for s in everything if s.id != target.id]
    if scope == "group":
        others = [
            s for s in others if s.student_group_id == target.student_group_id
        ]

    tids = {t.id for t in target.assigned_teachers.all()}
    budget = _day_budget(tenant, everything, tids)
    cur = _span(target)

    rows = []
    for other in others:
        sp = _span(other)
        if sp is None or other.is_locked or other.is_pinned:
            continue
        day, period, _n = sp
        if cur and cur[0] == day and cur[1] == period:
            continue
        # Bỏ hai buổi khỏi bản đồ bận rồi mới chấm, vì chúng sắp đổi chỗ.
        busy = _busy_map(everything, {target.id, other.id})
        verdict, reason = _judge(
            target, day, period, busy, day_budget=budget, other=other
        )
        rows.append(
            {
                "session_id": other.id,
                "day": day,
                "period": period,
                "duration_slots": int(other.duration_slots or 1),
                "module_code": other.module.code,
                "group_code": other.student_group.code,
                "teachers": [t.name for t in other.assigned_teachers.all()],
                "room": (
                    other.assigned_resource.code
                    if other.assigned_resource
                    else ""
                ),
                "verdict": verdict,
                "reason": reason,
            }
        )

    order = {
        VERDICT_GREEN: 0,
        VERDICT_ORANGE: 1,
        VERDICT_PINK: 2,
        VERDICT_PINK_DARK: 3,
    }
    rows.sort(key=lambda r: (order.get(r["verdict"], 9), r["day"], r["period"]))
    return {
        "session_id": target.id,
        "scope": scope,
        "candidates": rows,
        "green_count": sum(1 for r in rows if r["verdict"] == VERDICT_GREEN),
    }


class SwapIn(Schema):
    session_id: int
    other_id: int


@router.post("/schedule/{schedule_id}/swap")
def swap_sessions(request, schedule_id: int, payload: SwapIn):
    """Đổi chỗ hai buổi học. Từ chối nếu chấm ra trùng tiết."""
    _can_write(request)
    schedule = _get_or_404(Schedule, request, schedule_id, "Lịch")
    tenant = _tenant(request)
    qs = list(
        tenant.sessions.filter(schedule=schedule)
        .select_related("student_group")
        .prefetch_related("assigned_teachers")
    )
    by_id = {s.id: s for s in qs}
    a = by_id.get(payload.session_id)
    b = by_id.get(payload.other_id)
    if a is None or b is None:
        raise HttpError(404, "Buổi học không tồn tại")
    if a.id == b.id:
        raise HttpError(400, "Không thể đổi một buổi với chính nó")
    for s in (a, b):
        if s.is_locked or s.is_pinned:
            raise HttpError(400, "Buổi %s đã khoá hoặc đã ghim" % s.id)

    sp_a, sp_b = _span(a), _span(b)
    if sp_a is None or sp_b is None:
        raise HttpError(400, "Cả hai buổi đều phải đã được xếp tiết")

    busy = _busy_map(qs, {a.id, b.id})
    va, ra = _judge(a, sp_b[0], sp_b[1], busy)
    vb, rb = _judge(b, sp_a[0], sp_a[1], busy)
    for verdict, reason in ((va, ra), (vb, rb)):
        if verdict == VERDICT_PINK_DARK:
            raise HttpError(409, "Không đổi được: %s" % reason)

    with transaction.atomic():
        a.assigned_timeslot, b.assigned_timeslot = (
            dict(b.assigned_timeslot or {}),
            dict(a.assigned_timeslot or {}),
        )
        a.save(update_fields=["assigned_timeslot"])
        b.save(update_fields=["assigned_timeslot"])
        schedule.is_manual_edit = True
        schedule.save(update_fields=["is_manual_edit"])

    return {
        "swapped": True,
        "verdicts": [va, vb],
        "warnings": [r for v, r in ((va, ra), (vb, rb)) if v != VERDICT_GREEN],
    }


# --------------------------------------------------------------------------
# Khay tiết chờ xếp (FR-7.9)
# --------------------------------------------------------------------------

@router.get("/schedule/{schedule_id}/tray")
def list_tray(request, schedule_id: int):
    """Các buổi chưa có tiết — đang nằm chờ trong khay."""
    schedule = _get_or_404(Schedule, request, schedule_id, "Lịch")
    tenant = _tenant(request)
    rows = []
    qs = (
        tenant.sessions.filter(schedule=schedule)
        .select_related("module", "student_group", "assigned_resource")
        .prefetch_related("assigned_teachers")
    )
    for s in qs:
        if _span(s) is not None:
            continue
        rows.append(
            {
                "session_id": s.id,
                "module_code": s.module.code,
                "module_name": s.module.name,
                "group_code": s.student_group.code,
                "duration_slots": int(s.duration_slots or 1),
                "session_type": s.session_type,
                "room": (
                    s.assigned_resource.code if s.assigned_resource else ""
                ),
                "teachers": [t.name for t in s.assigned_teachers.all()],
            }
        )
    rows.sort(key=lambda r: (r["group_code"], r["module_code"]))
    return {"schedule_id": schedule.id, "tray": rows, "count": len(rows)}


class TrayMoveIn(Schema):
    session_id: int


@router.post("/schedule/{schedule_id}/tray")
def push_to_tray(request, schedule_id: int, payload: TrayMoveIn):
    """Kéo một buổi ra khỏi lưới, để đó xếp lại sau."""
    _can_write(request)
    schedule = _get_or_404(Schedule, request, schedule_id, "Lịch")
    tenant = _tenant(request)
    s = tenant.sessions.filter(
        id=payload.session_id, schedule=schedule
    ).first()
    if s is None:
        raise HttpError(404, "Buổi học không tồn tại")
    if s.is_locked or s.is_pinned:
        raise HttpError(400, "Buổi đã khoá hoặc đã ghim nên không gỡ được")
    if _span(s) is None:
        return {"session_id": s.id, "in_tray": True, "detail": "Đã ở trong khay"}

    s.assigned_timeslot = None
    s.save(update_fields=["assigned_timeslot"])
    schedule.is_manual_edit = True
    schedule.save(update_fields=["is_manual_edit"])
    return {"session_id": s.id, "in_tray": True}


class TrayPlaceIn(Schema):
    session_id: int
    day: int
    period: int


@router.post("/schedule/{schedule_id}/tray/place")
def place_from_tray(request, schedule_id: int, payload: TrayPlaceIn):
    """Thả buổi từ khay vào một ô. Chỉ nhận ô trống (FR-7.9)."""
    _can_write(request)
    schedule = _get_or_404(Schedule, request, schedule_id, "Lịch")
    tenant = _tenant(request)
    qs = list(
        tenant.sessions.filter(schedule=schedule)
        .select_related("student_group")
        .prefetch_related("assigned_teachers")
    )
    by_id = {s.id: s for s in qs}
    s = by_id.get(payload.session_id)
    if s is None:
        raise HttpError(404, "Buổi học không tồn tại")
    if s.is_locked or s.is_pinned:
        raise HttpError(400, "Buổi đã khoá hoặc đã ghim")
    if payload.day < 0 or payload.period < 0:
        raise HttpError(400, "Vị trí không hợp lệ")

    from scheduler import horizon as horizon_mod

    cfg = horizon_mod.normalize((tenant.config_json or {}).get("horizon"))
    n = max(1, int(s.duration_slots or 1))
    if payload.period + n > cfg["periods_per_day"]:
        raise HttpError(
            400,
            "Buổi dài %d tiết nên không đặt vừa từ tiết %d"
            % (n, payload.period + 1),
        )
    if payload.day >= len(cfg["days"]):
        raise HttpError(400, "Ngày nằm ngoài khung thời gian")

    busy = _busy_map(qs, {s.id})
    verdict, reason = _judge(s, payload.day, payload.period, busy)
    if verdict == VERDICT_PINK_DARK:
        raise HttpError(409, "Ô này không trống: %s" % reason)

    s.assigned_timeslot = {"day": payload.day, "period": payload.period}
    s.save(update_fields=["assigned_timeslot"])
    schedule.is_manual_edit = True
    schedule.save(update_fields=["is_manual_edit"])
    return {
        "session_id": s.id,
        "in_tray": False,
        "day": payload.day,
        "period": payload.period,
        "verdict": verdict,
        "warning": "" if verdict == VERDICT_GREEN else reason,
    }


# --------------------------------------------------------------------------
# Dừng bộ giải
# --------------------------------------------------------------------------

@router.post("/solve/{job_id}/stop")
def stop_solve(request, job_id: str):
    """Yêu cầu bộ giải dừng, giữ nguyên phương án đã tìm được.

    CP-SAT chỉ kiểm tra được yêu cầu dừng mỗi khi tìm ra nghiệm mới, nên
    lệnh có độ trễ tới nghiệm kế tiếp — thường vài giây.
    """
    from django.core.exceptions import ValidationError

    from scheduler.models import SolveJob

    _require(request, {"admin", "registrar"})
    try:
        job = SolveJob.objects.get(id=job_id)
    except (SolveJob.DoesNotExist, ValidationError, ValueError, TypeError):
        raise HttpError(404, "Phiên chạy không tồn tại")
    if job.tenant_id != request.auth["tenant_id"]:
        raise HttpError(404, "Phiên chạy không tồn tại")

    if job.status in (SolveJob.Status.SOLVED, SolveJob.Status.FAILED):
        return {
            "job_id": str(job.id),
            "status": job.status,
            "stopped": False,
            "detail": "Phiên chạy đã kết thúc",
        }

    job.stop_requested = True
    job.save(update_fields=["stop_requested"])
    return {"job_id": str(job.id), "status": job.status, "stopped": True}


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
