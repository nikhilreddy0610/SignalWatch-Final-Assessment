from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import JWT_ALGORITHM, JWT_SECRET
from app.models import Role

security = HTTPBearer(auto_error=False)


def create_token(tenant_id: str, user_id: str, role: str | Role) -> str:
    now = datetime.utcnow()
    role_name = role.value if isinstance(role, Role) else str(role).upper()
    if role_name.startswith("ROLE."):
        role_name = role_name.split(".", 1)[1]
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role": role_name,
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = cast(dict[str, Any], jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]))
        payload["role"] = str(payload.get("role", "")).upper()
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("role") not in (Role.ADMIN.value, Role.REGULAR_USER.value):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role in token")
    return payload


async def get_current_user_from_request(request: Request) -> dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if payload.get("role") not in (Role.ADMIN.value, Role.REGULAR_USER.value):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role in token")
    return payload
