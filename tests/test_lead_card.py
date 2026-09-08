import uuid

from app.models.enums import (
    AffiliateEventType,
    CommunicationChannel,
    CommunicationDirection,
    TrackingEventType,
    UserRole,
)
from tests.conftest import auth_headers, make_user


async def test_lead_card_returns_five_blocks(client, db_session):
    from app.crud.affiliate_event import list_affiliate_events_by_lead  # noqa: F401
    from app.models.affiliate_event import AffiliateEvent
    from app.models.communication import Communication
    from app.models.tracking_event import TrackingEvent

    admin = await make_user(db_session, UserRole.admin)
    sm = await make_user(db_session, UserRole.sales_manager)

    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm.id)}, headers=auth_headers(admin)
    )

    db_session.add(
        TrackingEvent(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            event_type=TrackingEventType.click,
            click_id="click-card-1",
            campaign_id="camp-card",
            raw_payload={},
        )
    )
    db_session.add(
        Communication(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            channel=CommunicationChannel.telegram,
            direction=CommunicationDirection.inbound,
            message_text="hello",
        )
    )
    db_session.add(
        AffiliateEvent(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            external_event_id="ext-1",
            event_type=AffiliateEventType.registration,
            raw_payload={},
        )
    )
    await db_session.commit()

    resp = await client.get(f"/api/v1/leads/{lead_id}/card", headers=auth_headers(admin))
    assert resp.status_code == 200
    body = resp.json()

    assert body["profile"]["lead_id"] == lead_id
    assert body["acquisition"]["campaign_id"] == "camp-card"
    assert body["manager"]["id"] == str(sm.id)
    assert len(body["communications"]) == 1
    assert body["communications"][0]["message_text"] == "hello"
    assert len(body["affiliate"]) == 1
    assert body["affiliate"][0]["event_type"] == "registration"


async def test_lead_card_forbidden_for_other_sales_manager(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    sm1 = await make_user(db_session, UserRole.sales_manager)
    sm2 = await make_user(db_session, UserRole.sales_manager)

    create_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]
    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm1.id)}, headers=auth_headers(admin)
    )

    resp = await client.get(f"/api/v1/leads/{lead_id}/card", headers=auth_headers(sm2))
    assert resp.status_code == 403


async def test_lead_communications_endpoint(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post("/api/v1/leads", json={"geo": "MA"}, headers=auth_headers(admin))
    lead_id = create_resp.json()["lead_id"]

    resp = await client.get(f"/api/v1/leads/{lead_id}/communications", headers=auth_headers(admin))
    assert resp.status_code == 200
    assert resp.json()["items"] == []
