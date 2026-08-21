import logging

import jwt
from django.conf import settings
from ninja.errors import HttpError

from scheduler.middleware import set_current_tenant
from scheduler.models import Tenant

logger = logging.getLogger(__name__)

TENANT_CLAIM = "tenant_id"
DEPLOYMENT_CLAIM = "deployment_id"

BEARER_PREFIX = "Bearer "


def decode_token(raw_token: str) -> dict:
    key = settings.JWT_SIGNING_KEY
    options = {
        "require": ["exp"],
        "verify_signature": True,
        "verify_exp": True,
    }
    issuer = getattr(settings, "JWT_ISSUER", "") or ""
    audience = getattr(settings, "JWT_AUDIENCE", "") or ""
    options["verify_iss"] = bool(issuer)
    options["verify_aud"] = bool(audience)

    kwargs = {"algorithms": ["HS256"], "options": options}
    if issuer:
        kwargs["issuer"] = issuer
    if audience:
        kwargs["audience"] = audience

    return jwt.decode(raw_token, key, **kwargs)


def tenant_auth(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith(BEARER_PREFIX):
        raise HttpError(401, "Authorization Bearer header required")
    raw_token = header[len(BEARER_PREFIX):].strip()
    if not raw_token:
        raise HttpError(401, "Empty bearer token")

    try:
        claims = decode_token(raw_token)
    except jwt.ExpiredSignatureError:
        raise HttpError(401, "Token expired")
    except jwt.PyJWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise HttpError(401, "Invalid token")

    tenant_id = claims.get(TENANT_CLAIM)
    if not tenant_id:
        raise HttpError(401, "Missing tenant_id claim")

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except (Tenant.DoesNotExist, ValueError, TypeError):
        logger.warning("JWT tenant not found in DB: %s", tenant_id)
        raise HttpError(403, "Unknown tenant")

    request.tenant_id = tenant.id
    request.tenant = tenant
    request.jwt_claims = claims
    set_current_tenant(tenant.id)

    # Vai trò lấy từ token; token cũ chưa có claim này thì coi như Phòng
    # Đào tạo để không khoá mất người dùng đang đăng nhập.
    role = claims.get("role") or "registrar"

    return {
        "tenant_id": tenant.id,
        "deployment_id": claims.get(DEPLOYMENT_CLAIM),
        "claims": claims,
        "tenant": tenant,
        "role": role,
        "email": claims.get("email"),
    }
