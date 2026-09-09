from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


async def test_send_communication_requires_telegram_user_id(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    resp = await client.post(
        f"/api/v1/leads/{lead_id}/communications", json={"message_text": "hi"}, headers=auth_headers(admin)
    )
    assert resp.status_code == 400


async def test_send_communication_success(client, db_session):
    import uuid

    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    # Привязываем telegram_user_id напрямую через входящий webhook-подобный сценарий не нужен -
    # проще проставить click/lead напрямую в БД для теста.
    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.telegram_user_id = "tg-comm-1"
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/leads/{lead_id}/communications",
        json={"message_text": "Здравствуйте!"},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["direction"] == "outbound"
    assert body["message_text"] == "Здравствуйте!"
    assert body["manager_id"] == str(admin.id)


async def test_sales_manager_cannot_send_to_others_lead(client, db_session):
    import uuid

    admin = await make_user(db_session, UserRole.admin)
    sm1 = await make_user(db_session, UserRole.sales_manager)
    sm2 = await make_user(db_session, UserRole.sales_manager)

    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.telegram_user_id = "tg-comm-2"
    lead.assigned_manager_id = sm1.id
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/leads/{lead_id}/communications", json={"message_text": "hi"}, headers=auth_headers(sm2)
    )
    assert resp.status_code == 403
