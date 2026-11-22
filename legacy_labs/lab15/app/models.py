from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    REGULAR_USER = "REGULAR_USER"


class DemoTokenRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier associated with the user")
    user_id: str = Field(..., description="User identifier for the token")
    role: Role = Field(default=Role.REGULAR_USER, description="User role in the tenant")


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    priority: Literal["low", "medium", "high"] = "medium"
    status: Literal["open", "in_progress", "completed", "blocked"] = "open"


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    priority: Optional[Literal["low", "medium", "high"]] = None
    status: Optional[Literal["open", "in_progress", "completed", "blocked"]] = None


class TaskRecord(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    title: str
    description: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


class TokenPayload(BaseModel):
    tenant_id: str
    user_id: str
    role: Role
    exp: int
    iat: int
    token_type: str = "access"
