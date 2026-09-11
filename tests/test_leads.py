from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


async def test_create_lead_as_admin(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post(
        "/api/v1/leads",
        json={"geo": "SY", "language": "ar", "source_channel": "organic"},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201
    assert resp.json()["geo"] == "SY"


async def test_create_lead_as_sales_manager_allowed(client, db_session):
    sm = await make_user(db_session, UserRole.sales_manager)
    resp = await client.post(
        "/api/v1/leads", json={"geo": "MA"}, headers=auth_headers(sm)
    )
    assert resp.status_code == 201


async def test_create_lead_as_analyst_forbidden(client, db_session):
    analyst = await make_user(db_session, UserRole.analyst)
    resp = await client.post("/api/v1/leads", json={"geo": "SA"}, headers=auth_headers(analyst))
    assert resp.status_code == 403


async def test_get_lead_not_found(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.get(
        "/api/v1/leads/00000000-0000-0000-0000-000000000000", headers=auth_headers(admin)
    )
    assert resp.status_code == 404


async def test_sales_manager_cannot_view_other_managers_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    sm1 = await make_user(db_session, UserRole.sales_manager)
    sm2 = await make_user(db_session, UserRole.sales_manager)

    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    assign_resp = await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm1.id)}, headers=auth_headers(admin)
    )
    assert assign_resp.status_code == 200

    forbidden_resp = await client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers(sm2))
    assert forbidden_resp.status_code == 403

    allowed_resp = await client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers(sm1))
    assert allowed_resp.status_code == 200


async def test_assign_lead_forbidden_for_sales_manager(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    sm = await make_user(db_session, UserRole.sales_manager)

    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    resp = await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm.id)}, headers=auth_headers(sm)
    )
    assert resp.status_code == 403


async def test_update_lead_status_writes_audit_log(client, db_session):
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    patch_resp = await client.patch(
        f"/api/v1/leads/{lead_id}", json={"status": "contacted"}, headers=auth_headers(admin)
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "contacted"

    result = await db_session.execute(select(AuditLog).where(AuditLog.entity_id == lead_id))
    logs = result.scalars().all()
    actions = {log.action for log in logs}
    assert "lead_updated" in actions


async def test_list_leads_pagination_cursor(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    for i in range(3):
        await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))

    resp = await client.get("/api/v1/leads?limit=2", headers=auth_headers(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["next_cursor"] is not None

    resp2 = await client.get(f"/api/v1/leads?limit=2&cursor={body['next_cursor']}", headers=auth_headers(admin))
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 1


async def test_unauthenticated_request_rejected(client):
    resp = await client.get("/api/v1/leads")
    assert resp.status_code == 401


async def test_mop_lead_can_view_all_leads(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    mop_lead = await make_user(db_session, UserRole.mop_lead)

    await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))

    resp = await client.get("/api/v1/leads", headers=auth_headers(mop_lead))
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


async def test_mop_lead_cannot_create_or_assign_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    mop_lead = await make_user(db_session, UserRole.mop_lead)

    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(mop_lead))
    assert create_resp.status_code == 403

    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    assign_resp = await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(mop_lead.id)}, headers=auth_headers(mop_lead)
    )
    assert assign_resp.status_code == 403


async def test_admin_can_delete_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    resp = await client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers(admin))
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers(admin))
    assert get_resp.status_code == 404


async def test_non_admin_cannot_delete_lead(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    affman = await make_user(db_session, UserRole.affiliate_manager)
    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    resp = await client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers(affman))
    assert resp.status_code == 403


async def test_delete_lead_detaches_affiliate_events_instead_of_losing_them(client, db_session):
    import uuid

    from app.models.affiliate_event import AffiliateEvent
    from app.models.enums import AffiliateEventType

    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    event = AffiliateEvent(
        id=uuid.uuid4(),
        lead_id=uuid.UUID(lead_id),
        partner="binolla",
        external_event_id="del-test-1",
        event_type=AffiliateEventType.ftd,
        raw_payload={},
    )
    db_session.add(event)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers(admin))
    assert resp.status_code == 204

    await db_session.refresh(event)
    assert event.lead_id is None
