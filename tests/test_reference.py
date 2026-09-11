from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


async def test_admin_can_create_partner(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post("/api/v1/partners", json={"name": "PocketOption"}, headers=auth_headers(admin))
    assert resp.status_code == 201
    assert resp.json()["name"] == "PocketOption"
    assert resp.json()["is_active"] is True


async def test_non_admin_cannot_create_partner(client, db_session):
    sm = await make_user(db_session, UserRole.sales_manager)
    resp = await client.post("/api/v1/partners", json={"name": "PocketOption"}, headers=auth_headers(sm))
    assert resp.status_code == 403


async def test_any_authenticated_user_can_list_partners(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    await client.post("/api/v1/partners", json={"name": "Binolla"}, headers=auth_headers(admin))

    analyst = await make_user(db_session, UserRole.analyst)
    resp = await client.get("/api/v1/partners", headers=auth_headers(analyst))
    assert resp.status_code == 200
    assert any(p["name"] == "Binolla" for p in resp.json())


async def test_duplicate_partner_name_rejected(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    await client.post("/api/v1/partners", json={"name": "Binolla"}, headers=auth_headers(admin))
    resp = await client.post("/api/v1/partners", json={"name": "Binolla"}, headers=auth_headers(admin))
    assert resp.status_code == 409


async def test_admin_can_deactivate_partner(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post("/api/v1/partners", json={"name": "Binolla"}, headers=auth_headers(admin))
    partner_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/partners/{partner_id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_admin_can_create_channel(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post("/api/v1/channels", json={"name": "MENA-Karim"}, headers=auth_headers(admin))
    assert resp.status_code == 201
    assert resp.json()["name"] == "MENA-Karim"


async def test_non_admin_cannot_create_channel(client, db_session):
    analyst = await make_user(db_session, UserRole.analyst)
    resp = await client.post("/api/v1/channels", json={"name": "MENA-Karim"}, headers=auth_headers(analyst))
    assert resp.status_code == 403


async def test_unauthenticated_cannot_list_partners(client):
    resp = await client.get("/api/v1/partners")
    assert resp.status_code == 401
