"""
NinjaAPI instance and project-level endpoints.
"""

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from ninja import File, NinjaAPI, Schema, UploadedFile
from ninja.errors import HttpError

from scheduler import excel_parser, templates, validator
from scheduler.auth import tenant_auth
from scheduler.models import (
    Module,
    Resource,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    TeacherModule,
)
from scheduler.scoping import scoped_queryset
from scheduler.solver import objectives


api = NinjaAPI(title="evo-scheduler-service API", version="1.0.0")


@api.get("/health")
def health(request):
    return {"status": "ok"}


class MeResponse(Schema):
    tenant_id: int
    deployment_id: str | None = None
    tenant_code: str
    tenant_name: str
    claims: dict


@api.get("/me", auth=tenant_auth, response=MeResponse)
def me(request):
    auth_payload = request.auth
    tenant = auth_payload["tenant"]
    return {
        "tenant_id": tenant.id,
        "deployment_id": auth_payload.get("deployment_id"),
        "tenant_code": tenant.code,
        "tenant_name": tenant.name,
        "claims": auth_payload.get("claims", {}),
    }


class TeacherOut(Schema):
    code: str
    name: str


@api.get("/teachers", auth=tenant_auth, response=list[TeacherOut])
def list_teachers(request):
    qs = scoped_queryset(Teacher)
    return [{"code": t.code, "name": t.name} for t in qs]


class WeightsIn(Schema):
    weights: dict


class WeightsOut(Schema):
    schedule_id: int
    weights: dict


def _get_tenant_schedule(request, schedule_id):
    try:
        schedule = Schedule.objects.get(id=schedule_id)
    except (Schedule.DoesNotExist, ValueError, TypeError):
        raise HttpError(404, "schedule not found")
    if schedule.tenant_id != request.auth["tenant_id"]:
        raise HttpError(404, "schedule not found")
    return schedule


@api.get("/schedule/{schedule_id}/weights", auth=tenant_auth, response=WeightsOut)
def get_schedule_weights(request, schedule_id):
    schedule = _get_tenant_schedule(request, schedule_id)
    merged = objectives.merge_weights(schedule.weights_json)
    return {"schedule_id": schedule.id, "weights": merged}


@api.put("/schedule/{schedule_id}/weights", auth=tenant_auth, response=WeightsOut)
def update_schedule_weights(request, schedule_id, payload: WeightsIn):
    schedule = _get_tenant_schedule(request, schedule_id)
    incoming = payload.weights or {}
    cleaned = {}
    for k, v in incoming.items():
        if k not in objectives.KNOWN_WEIGHT_KEYS:
            raise HttpError(400, "unknown weight key: %s" % k)
        try:
            iv = int(v)
        except (TypeError, ValueError):
            raise HttpError(400, "invalid weight value for %s: %s" % (k, v))
        if iv < 0:
            raise HttpError(400, "weight must be >= 0: %s" % k)
        cleaned[k] = iv
    stored = dict(schedule.weights_json or {})
    stored.update(cleaned)
    schedule.weights_json = stored
    schedule.save(update_fields=["weights_json"])
    merged = objectives.merge_weights(schedule.weights_json)
    return {"schedule_id": schedule.id, "weights": merged}


XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
SAMPLE_LIMIT = 3


def _summarize(parsed, issues):
    row_counts = {name: len(parsed[name]) for name in excel_parser.SHEET_NAMES}
    sample = {
        name: parsed[name][:SAMPLE_LIMIT] for name in excel_parser.SHEET_NAMES
    }
    errors = [i for i in issues if i["severity"] == validator.SEVERITY_ERROR]
    warnings = [i for i in issues if i["severity"] == validator.SEVERITY_WARNING]
    return {
        "row_counts": row_counts,
        "issues": issues,
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "sample": sample,
    }


def _read_upload(file: UploadedFile):
    data = file.read()
    if hasattr(file, "seek"):
        try:
            file.seek(0)
        except Exception:
            pass
    if not data:
        raise HttpError(400, "Empty file upload")
    try:
        return excel_parser.parse_bytes(data)
    except Exception as exc:
        raise HttpError(400, "Could not read workbook: %s" % exc)


@api.get("/import/template", auth=tenant_auth, url_name="import_template")
def import_template(request):
    payload = templates.generate_template()
    response = HttpResponse(payload, content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = 'attachment; filename="import_template.xlsx"'
    response["Content-Length"] = str(len(payload))
    return response


@api.post("/import/upload", auth=tenant_auth, url_name="import_upload")
def import_upload(request, file: UploadedFile = File(...)):
    parsed = _read_upload(file)
    issues = validator.validate(parsed)
    return JsonResponse(_summarize(parsed, issues))


@api.post("/import/commit", auth=tenant_auth, url_name="import_commit")
def import_commit(request, file: UploadedFile = File(...)):
    parsed = _read_upload(file)
    issues = validator.validate(parsed)
    if validator.has_errors(issues):
        return JsonResponse(
            {
                "detail": "validation errors",
                "issues": issues,
                "errors_count": sum(
                    1 for i in issues if i["severity"] == validator.SEVERITY_ERROR
                ),
                "created": {},
            },
            status=400,
        )

    tenant = request.auth["tenant"]
    created = _persist(parsed, tenant)
    return JsonResponse({"created": created, "issues": issues}, status=201)


def _persist(parsed, tenant):
    from scheduler.excel_parser import to_int, to_list, to_str

    teachers = {}
    student_groups = {}
    resources = {}
    modules = {}
    created = {
        "teachers": 0,
        "student_groups": 0,
        "resources": 0,
        "modules": 0,
        "teacher_modules": 0,
        "sessions": 0,
    }

    with transaction.atomic():
        for r in parsed["Teachers"]:
            code = to_str(r.get("code"))
            blocks = [b.lower() for b in to_list(r.get("blocks"))]
            quota = None
            if r.get("quota_standard_hours") not in (None, ""):
                quota = to_int(r.get("quota_standard_hours"))
            teacher = Teacher.objects.create(
                tenant=tenant,
                code=code,
                name=to_str(r.get("name")),
                blocks=blocks,
                quota_standard_hours=quota,
            )
            teachers[code] = teacher
            created["teachers"] += 1

        for r in parsed["StudentGroups"]:
            code = to_str(r.get("code"))
            sg = StudentGroup.objects.create(
                tenant=tenant,
                code=code,
                name=to_str(r.get("name")),
                enrollment_type=to_str(r.get("enrollment_type")).lower(),
                size=to_int(r.get("size")) or 0,
            )
            student_groups[code] = sg
            created["student_groups"] += 1

        for r in parsed["Resources"]:
            code = to_str(r.get("code"))
            quantity = to_int(r.get("quantity")) or 0
            available = to_int(r.get("available_quantity"))
            if available is None:
                available = quantity
            resource = Resource.objects.create(
                tenant=tenant,
                code=code,
                name=to_str(r.get("name")),
                type=to_str(r.get("type")).lower(),
                capacity=to_int(r.get("capacity")) or 0,
                quantity=quantity,
                available_quantity=available,
            )
            resources[code] = resource
            created["resources"] += 1

        for r in parsed["Modules"]:
            code = to_str(r.get("code"))
            sg_code = to_str(r.get("student_group"))
            module = Module.objects.create(
                tenant=tenant,
                code=code,
                name=to_str(r.get("name")),
                theory_hours=to_int(r.get("theory_hours")) or 0,
                practice_hours=to_int(r.get("practice_hours")) or 0,
                student_group=student_groups.get(sg_code) if sg_code else None,
            )
            modules[code] = module
            created["modules"] += 1

        for r in parsed["TeacherModule"]:
            teacher = teachers.get(to_str(r.get("teacher_code")))
            module = modules.get(to_str(r.get("module_code")))
            if teacher and module:
                TeacherModule.objects.create(
                    tenant=tenant, teacher=teacher, module=module
                )
                created["teacher_modules"] += 1

        for r in parsed["FixedSessions"]:
            module = modules.get(to_str(r.get("module_code")))
            sg = student_groups.get(to_str(r.get("student_group_code")))
            resource_code = to_str(r.get("resource_code"))
            resource = resources.get(resource_code) if resource_code else None
            if not (module and sg):
                continue
            session = Session.objects.create(
                tenant=tenant,
                module=module,
                student_group=sg,
                session_type=to_str(r.get("session_type")).lower(),
                duration_slots=to_int(r.get("duration_slots")) or 1,
                tier=to_str(r.get("tier")).lower(),
                assigned_resource=resource,
            )
            teacher_codes = to_list(r.get("teacher_codes"))
            if teacher_codes:
                session.assigned_teachers.set(
                    [teachers[c].id for c in teacher_codes if c in teachers]
                )
            created["sessions"] += 1

    return created
