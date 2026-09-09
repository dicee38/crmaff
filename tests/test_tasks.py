from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


async def test_admin_creates_task_for_any_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    resp = await client.post(
        "/api/v1/tasks", json={"lead_id": lead_id, "title": "Позвонить лиду"}, headers=auth_headers(admin)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Позвонить лиду"
    assert body["status"] == "open"
    assert body["manager_id"] == str(admin.id)


async def test_sales_manager_cannot_create_task_for_others_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    sm1 = await make_user(db_session, UserRole.sales_manager)
    sm2 = await make_user(db_session, UserRole.sales_manager)

    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]
    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm1.id)}, headers=auth_headers(admin)
    )

    resp = await client.post(
        "/api/v1/tasks", json={"lead_id": lead_id, "title": "Task"}, headers=auth_headers(sm2)
    )
    assert resp.status_code == 403

    ok_resp = await client.post(
        "/api/v1/tasks", json={"lead_id": lead_id, "title": "Task"}, headers=auth_headers(sm1)
    )
    assert ok_resp.status_code == 201


async def test_update_task_status_to_done(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]
    task_resp = await client.post(
        "/api/v1/tasks", json={"lead_id": lead_id, "title": "Task"}, headers=auth_headers(admin)
    )
    task_id = task_resp.json()["id"]

    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=auth_headers(admin))
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


async def test_task_not_found(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.get(
        "/api/v1/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers(admin)
    )
    assert resp.status_code == 404


async def test_list_tasks_filtered_by_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead1 = (await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))).json()["lead_id"]
    lead2 = (await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))).json()["lead_id"]

    await client.post("/api/v1/tasks", json={"lead_id": lead1, "title": "A"}, headers=auth_headers(admin))
    await client.post("/api/v1/tasks", json={"lead_id": lead2, "title": "B"}, headers=auth_headers(admin))

    resp = await client.get(f"/api/v1/tasks?lead_id={lead1}", headers=auth_headers(admin))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["lead_id"] == lead1


async def test_unauthenticated_task_list_rejected(client):
    resp = await client.get("/api/v1/tasks")
    assert resp.status_code == 401
