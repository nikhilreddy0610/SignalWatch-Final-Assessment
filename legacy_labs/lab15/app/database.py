from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection

from app.config import DB_NAME, MONGO_URI, RATE_LIMIT_WINDOW_SECONDS


def get_client() -> MongoClient:
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_db():
    return get_client()[DB_NAME]


def ensure_indexes() -> None:
    db = get_db()
    tasks: Collection = db["tasks"]
    tasks.create_index([("tenant_id", ASCENDING), ("created_at", ASCENDING)], name="tenant_created_idx")
    tasks.create_index([("tenant_id", ASCENDING), ("user_id", ASCENDING)], name="tenant_user_idx")
    tasks.create_index([("tenant_id", ASCENDING), ("status", ASCENDING)], name="tenant_status_idx")

    rate_limits: Collection = db["rate_limits"]
    rate_limits.create_index([("tenant_id", ASCENDING), ("window_start", ASCENDING)], unique=True, name="tenant_window_idx")
    rate_limits.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expiry_idx")


def serialize_task(task: dict[str, Any] | None) -> dict[str, Any] | None:
    if task is None:
        return None
    item = dict(task)
    item["id"] = str(item.pop("_id"))
    if "created_at" in item and not isinstance(item["created_at"], str):
        item["created_at"] = item["created_at"].isoformat()
    if "updated_at" in item and not isinstance(item["updated_at"], str):
        item["updated_at"] = item["updated_at"].isoformat()
    return item


def make_task_document(payload: dict[str, Any], tenant_id: str, user_id: str) -> dict[str, Any]:
    now = datetime.utcnow()
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "title": payload["title"],
        "description": payload["description"],
        "priority": payload.get("priority", "medium"),
        "status": payload.get("status", "open"),
        "created_at": now,
        "updated_at": now,
    }


def check_rate_limit(tenant_id: str, limit: int = 30, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> bool:
    db = get_db()
    collection: Collection = db["rate_limits"]
    now = datetime.utcnow()
    window_start = int(now.timestamp() // window_seconds) * window_seconds
    expires_at = now + timedelta(seconds=window_seconds)

    doc = collection.find_one_and_update(
        {"tenant_id": tenant_id, "window_start": window_start},
        {"$inc": {"count": 1}, "$setOnInsert": {"window_start": window_start, "expires_at": expires_at}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return True
    if doc.get("count", 0) > limit:
        return False
    return True
