"""
NinjaAPI instance and project-level endpoints.
"""

from ninja import NinjaAPI, Schema

from scheduler.auth import tenant_auth
from scheduler.scoping import scoped_queryset
from scheduler.models import Teacher


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
