"""
NinjaAPI instance and project-level endpoints.
"""

from ninja import NinjaAPI, Schema
from ninja.errors import HttpError

from scheduler.auth import tenant_auth
from scheduler.scoping import scoped_queryset
from scheduler.models import Teacher, Schedule
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
