from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db() -> None:
    db = get_db()
    db["tasks"].delete_many({})
    db["rate_limits"].delete_many({})


def get_token(tenant_id: str, user_id: str, role: str) -> str:
    response = client.post(
        "/auth/demo-token",
        json={"tenant_id": tenant_id, "user_id": user_id, "role": role},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def make_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_create_list_update_delete_task() -> None:
    token = get_token("tenant_a", "admin_1", "ADMIN")
    headers = make_headers(token)

    create_response = client.post(
        "/tasks/",
        json={"title": "Plan sprint", "description": "Plan next sprint items", "priority": "high"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    payload = create_response.json()
    task_id = payload["task"]["id"]

    list_response = client.get("/tasks/", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/tasks/{task_id}",
        json={"status": "completed", "priority": "low"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["task"]["status"] == "completed"

    delete_response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert delete_response.status_code == 200


def test_tenant_isolation_blocked() -> None:
    tenant_a_admin = get_token("tenant_a", "admin_a", "ADMIN")
    tenant_b_admin = get_token("tenant_b", "admin_b", "ADMIN")

    task_response = client.post(
        "/tasks/",
        json={"title": "Alpha task", "description": "task for tenant A", "priority": "medium"},
        headers=make_headers(tenant_a_admin),
    )
    task_id = task_response.json()["task"]["id"]

    listing_response = client.get("/tasks/", headers=make_headers(tenant_b_admin))
    assert listing_response.status_code == 200
    assert listing_response.json() == []

    cross_update = client.put(
        f"/tasks/{task_id}",
        json={"title": "Hacked title"},
        headers=make_headers(tenant_b_admin),
    )
    assert cross_update.status_code == 404


def test_regular_user_permissions_are_scoped_to_own_tasks() -> None:
    user_a = get_token("tenant_a", "user_a", "REGULAR_USER")
    user_b = get_token("tenant_a", "user_b", "REGULAR_USER")

    task_a = client.post(
        "/tasks/",
        json={"title": "User A task", "description": "owned by A", "priority": "high"},
        headers=make_headers(user_a),
    )
    task_b = client.post(
        "/tasks/",
        json={"title": "User B task", "description": "owned by B", "priority": "low"},
        headers=make_headers(user_b),
    )
    task_a_id = task_a.json()["task"]["id"]
    task_b_id = task_b.json()["task"]["id"]

    a_list = client.get("/tasks/", headers=make_headers(user_a))
    assert a_list.status_code == 200
    ids_a = {item["id"] for item in a_list.json()}
    assert task_a_id in ids_a and task_b_id not in ids_a

    blocked_update = client.put(
        f"/tasks/{task_b_id}",
        json={"title": "tampered"},
        headers=make_headers(user_a),
    )
    assert blocked_update.status_code == 404

    allowed_update = client.put(
        f"/tasks/{task_a_id}",
        json={"status": "in_progress"},
        headers=make_headers(user_a),
    )
    assert allowed_update.status_code == 200
    assert allowed_update.json()["task"]["status"] == "in_progress"


def test_rate_limit_is_enforced() -> None:
    token = get_token("tenant_rate", "user_rate", "REGULAR_USER")
    headers = make_headers(token)

    for idx in range(30):
        response = client.post(
            "/tasks/",
            json={"title": f"rate task {idx}", "description": "rate limit check", "priority": "low"},
            headers=headers,
        )
        assert response.status_code == 201, f"request {idx} unexpectedly failed: {response.text}"

    over_limit = client.post(
        "/tasks/",
        json={"title": "rate task limit", "description": "should be blocked", "priority": "low"},
        headers=headers,
    )
    assert over_limit.status_code == 429, over_limit.text


def test_admin_can_view_all_tasks_in_tenant() -> None:
    admin = get_token("tenant_admin", "admin_owner", "ADMIN")
    regular = get_token("tenant_admin", "regular_owner", "REGULAR_USER")

    client.post(
        "/tasks/",
        json={"title": "admin-created", "description": "by admin", "priority": "high"},
        headers=make_headers(admin),
    )
    client.post(
        "/tasks/",
        json={"title": "user-created", "description": "by user", "priority": "low"},
        headers=make_headers(regular),
    )

    response = client.get("/tasks/", headers=make_headers(admin))
    assert response.status_code == 200
    assert len(response.json()) == 2
