from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pymongo import ReturnDocument
from pymongo.collection import Collection

from app.auth import create_token, get_current_user, get_current_user_from_request
from app.config import RATE_LIMIT_PER_MINUTE, RATE_LIMIT_WINDOW_SECONDS
from app.database import check_rate_limit, ensure_indexes, get_db, serialize_task
from app.models import DemoTokenRequest, Role, TaskCreate, TaskRecord, TaskUpdate

app = FastAPI(title="Multi-Tenant SaaS API", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    ensure_indexes()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/demo-token")
def create_demo_auth_token(payload: DemoTokenRequest) -> dict[str, str]:
    token = create_token(payload.tenant_id, payload.user_id, payload.role)
    return {"access_token": token, "token_type": "bearer"}


def rate_limit_for_tenant(tenant_id: str) -> None:
    allowed = check_rate_limit(tenant_id, limit=RATE_LIMIT_PER_MINUTE, window_seconds=RATE_LIMIT_WINDOW_SECONDS)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this tenant.",
        )


@app.get("/tasks/")
def list_tasks(request: Request, current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    rate_limit_for_tenant(current_user["tenant_id"])
    db = get_db()
    query: dict[str, Any] = {"tenant_id": current_user["tenant_id"]}
    if current_user["role"] == Role.REGULAR_USER.value:
        query["user_id"] = current_user["user_id"]
    tasks = list(db["tasks"].find(query).sort("created_at", -1))
    return [serialize_task(task) for task in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: str, request: Request, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    rate_limit_for_tenant(current_user["tenant_id"])
    db = get_db()
    query: dict[str, Any] = {"_id": ObjectId(task_id), "tenant_id": current_user["tenant_id"]}
    if current_user["role"] == Role.REGULAR_USER.value:
        query["user_id"] = current_user["user_id"]
    task = db["tasks"].find_one(query)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return serialize_task(task)


@app.post("/tasks/", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    rate_limit_for_tenant(current_user["tenant_id"])
    db = get_db()
    now = datetime.utcnow()
    task = {
        "tenant_id": current_user["tenant_id"],
        "user_id": current_user["user_id"],
        "title": payload.title,
        "description": payload.description,
        "priority": payload.priority,
        "status": payload.status,
        "created_at": now,
        "updated_at": now,
    }
    inserted = db["tasks"].insert_one(task)
    task["_id"] = inserted.inserted_id
    return {"message": "Task created", "task": serialize_task(task)}


@app.put("/tasks/{task_id}")
def update_task(task_id: str, updates: TaskUpdate, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    rate_limit_for_tenant(current_user["tenant_id"])
    query: dict[str, Any] = {"_id": ObjectId(task_id), "tenant_id": current_user["tenant_id"]}
    if current_user["role"] == Role.REGULAR_USER.value:
        query["user_id"] = current_user["user_id"]
    update_values = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}
    if not update_values:
        return {"message": "No fields to update", "task": None}
    update_values["updated_at"] = datetime.utcnow()
    db = get_db()
    result = db["tasks"].find_one_and_update(query, {"$set": update_values}, return_document=ReturnDocument.AFTER)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not allowed")
    return {"message": "Task updated", "task": serialize_task(result)}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    rate_limit_for_tenant(current_user["tenant_id"])
    query: dict[str, Any] = {"_id": ObjectId(task_id), "tenant_id": current_user["tenant_id"]}
    if current_user["role"] == Role.REGULAR_USER.value:
        query["user_id"] = current_user["user_id"]
    db = get_db()
    result = db["tasks"].delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not allowed")
    return {"message": "Task deleted"}


@app.get("/debug/tenant")
def debug_tenant(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "tenant_id": current_user["tenant_id"],
        "user_id": current_user["user_id"],
        "role": current_user["role"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
