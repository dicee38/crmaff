import uuid

from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user

SECRET = "test-binolla-secret"
BASE = "/api/v1/webhooks/binolla"


def _url(**params) -> str:
    params.setdefault("secret", SECRET)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE}?{query}"


async def _create_lead_with_click_id(client, db_session, click_id: str) -> str:
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.external_click_id = click_id
    await db_session.commit()
    return lead_id


async def test_binolla_webhook_secret_in_path_accepted(client, db_session):
    # Binolla-подобные UI автогенерируют query-строку из фиксированного набора
    # полей и не дают вписать свой ?secret=... - поэтому секрет также
    # принимается как сегмент пути перед стандартными query-параметрами.
    lead_id = await _create_lead_with_click_id(client, db_session, "click-path-secret-1")
    resp = await client.get(
        f"/api/v1/webhooks/binolla/{SECRET}?status=reg&eid=path-evt-1&cid=click-path-secret-1"
    )
    assert resp.status_code == 200
    assert resp.json()["lead_id"] == lead_id


async def test_binolla_webhook_wrong_path_secret_rejected(client):
    resp = await client.get("/api/v1/webhooks/binolla/wrong-secret?status=reg&eid=e1&cid=c1")
    assert resp.status_code == 401


async def test_binolla_webhook_invalid_secret_rejected(client):
    resp = await client.get(_url(secret="wrong", status="reg", eid="e1", cid="c1"))
    assert resp.status_code == 401


async def test_binolla_webhook_missing_fields_rejected(client):
    resp = await client.get(_url(status="reg"))
    assert resp.status_code == 400


async def test_binolla_webhook_registration_matches_lead_and_updates_status(client, db_session):
    lead_id = await _create_lead_with_click_id(client, db_session, "click-bin-1")

    resp = await client.get(_url(status="reg", eid="evt-1", cid="click-bin-1", uid="trader-1", sid="1", lid="28941"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead_id"] == lead_id
    assert body["unmatched"] is False

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.status.value == "registered"


async def test_binolla_webhook_ftd_sets_amount_and_status(client, db_session):
    lead_id = await _create_lead_with_click_id(client, db_session, "click-bin-2")

    resp = await client.get(_url(status="ftd", eid="evt-2", cid="click-bin-2", payout="150.50"))
    assert resp.status_code == 200

    from app.crud.affiliate_event import get_affiliate_event_by_external_id
    from app.crud.lead import get_lead

    event = await get_affiliate_event_by_external_id(db_session, "evt-2")
    assert float(event.amount) == 150.50
    assert event.event_type.value == "ftd"

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.status.value == "ftd"


async def test_binolla_webhook_status_does_not_regress(client, db_session):
    lead_id = await _create_lead_with_click_id(client, db_session, "click-bin-3")

    await client.get(_url(status="ftd", eid="evt-3a", cid="click-bin-3", payout="100"))
    # Поздний/повторный reg-постбэк после уже случившегося ftd не должен откатывать статус.
    await client.get(_url(status="reg", eid="evt-3b", cid="click-bin-3"))

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.status.value == "ftd"


async def test_binolla_webhook_unmatched_lead_not_dropped(client):
    resp = await client.get(_url(status="ftd", eid="evt-unmatched-1", cid="no-such-click-id", payout="50"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead_id"] is None
    assert body["unmatched"] is True

    from app.database import AsyncSessionLocal
    from app.crud.affiliate_event import get_affiliate_event_by_external_id

    async with AsyncSessionLocal() as db:
        event = await get_affiliate_event_by_external_id(db, "evt-unmatched-1")
        assert event is not None
        assert event.validation_flags == {"unmatched_lead": True}


async def test_binolla_webhook_idempotent_same_eid(client, db_session):
    lead_id = await _create_lead_with_click_id(client, db_session, "click-bin-4")

    resp1 = await client.get(_url(status="reg", eid="evt-dup-1", cid="click-bin-4"))
    resp2 = await client.get(_url(status="reg", eid="evt-dup-1", cid="click-bin-4"))
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["affiliate_event_id"] == resp2.json()["affiliate_event_id"]

    from sqlalchemy import select

    from app.models.affiliate_event import AffiliateEvent

    result = await db_session.execute(
        select(AffiliateEvent).where(AffiliateEvent.external_event_id == "evt-dup-1")
    )
    assert len(result.scalars().all()) == 1


async def test_binolla_webhook_unknown_status_rejected(client):
    resp = await client.get(_url(status="bogus", eid="evt-x", cid="click-x"))
    assert resp.status_code == 400
