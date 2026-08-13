from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password

TOKEN_TTL = timedelta(hours=12)
ALGORITHM = "HS256"


def hash_password(raw_password: str) -> str:
    return make_password(raw_password)


def verify_password(raw_password: str, encoded: str) -> bool:
    return check_password(raw_password, encoded)


def mint_token(user) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "tenant_id": str(user.tenant_id),
        "deployment_id": "self",
        "email": user.email,
        "name": user.name,
        "iat": int(now.timestamp()),
        "exp": int((now + TOKEN_TTL).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SIGNING_KEY, algorithm=ALGORITHM)
