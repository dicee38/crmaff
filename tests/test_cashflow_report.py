import json
import uuid

from app.core.signing import compute_hmac_signature
from app.crud.lead import get_lead
from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user

TRACK_SECRET = "test-track-secret"
BINOLLA_SECRET = "test-binolla-secret"


def _signed_click_kwargs(payload: dict) -> dict:
    body = json.dumps(payload).encode()
    signature = compute_hmac_signature(TRACK_SECRET, body)
    return {"content": body, "headers": {"Content-Type": "application/json", "X-Signature": signature}}


def _binolla_url(**params) -> str:
    params.setdefault("secret", BINOLLA_SECRET)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/api/v1/webhooks/binolla?{query}"


async def _setup_manager_with_activity(client, db_session, admin, click_id: str):
    manager = await make_user(db_session, UserRole.sales_manager, geo_coverage=["SY"], dialects=[])

    click_resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": click_id, "geo": "SY"})
    )
    lead_id = click_resp.json()["lead_id"]

    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(manager.id)}, headers=auth_headers(admin)
    )
    return manager, lead_id


async def test_cashflow_report_manager_breakdown(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    manager, lead_id = await _setup_manager_with_activity(client, db_session, admin, "cf-click-1")

    await client.get(_binolla_url(status="reg", eid="cf-evt-1", cid="cf-click-1"))
    await client.get(_binolla_url(status="ftd", eid="cf-evt-2", cid="cf-click-1", payout="100"))

    resp = await client.get("/api/v1/reports/mop-cashflow", headers=auth_headers(admin))
    assert resp.status_code == 200
    body = resp.json()

    assert body["total"]["reg"] >= 1
    assert body["total"]["fd_count"] >= 1
    assert float(body["total"]["fd_sum"]) >= 100.0

    manager_group = next((g for g in body["groups"] if g["key"] == str(manager.id)), None)
    assert manager_group is not None
    assert manager_group["reg"] == 1
    assert manager_group["fd_count"] == 1
    assert float(manager_group["cashflow"]) == 100.0
    assert manager_group["reg2fd_pct"] == 100.0


async def test_cashflow_report_sales_manager_sees_only_own_no_groups(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    manager, lead_id = await _setup_manager_with_activity(client, db_session, admin, "cf-click-sm")
    await client.get(_binolla_url(status="reg", eid="cf-evt-sm-1", cid="cf-click-sm"))

    resp = await client.get("/api/v1/reports/mop-cashflow", headers=auth_headers(manager))
    assert resp.status_code == 200
    body = resp.json()
    assert body["groups"] == []
    assert body["total"]["reg"] == 1


async def test_cashflow_report_forbidden_for_compliance(client, db_session):
    compliance = await make_user(db_session, UserRole.compliance)
    resp = await client.get("/api/v1/reports/mop-cashflow", headers=auth_headers(compliance))
    assert resp.status_code == 403


async def test_cashflow_report_allowed_for_mop_lead(client, db_session):
    mop_lead = await make_user(db_session, UserRole.mop_lead)
    resp = await client.get("/api/v1/reports/mop-cashflow", headers=auth_headers(mop_lead))
    assert resp.status_code == 200


async def test_cashflow_report_group_by_channel(client, db_session):
    admin = await make_user(db_session, UserRole.admin)

    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]
    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.external_click_id = "cf-channel-player"
    await db_session.commit()

    resp = await client.post(
        "/api/v1/actions",
        json={
            "player_id": "cf-channel-player",
            "partner_name": "Binolla",
            "channel": "MENA-KARIM",
            "event_type": "registration",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201

    report_resp = await client.get(
        "/api/v1/reports/mop-cashflow?group_by=channel", headers=auth_headers(admin)
    )
    assert report_resp.status_code == 200
    body = report_resp.json()
    channel_group = next((g for g in body["groups"] if g["key"] == "MENA-KARIM"), None)
    assert channel_group is not None
    assert channel_group["reg"] == 1
    assert channel_group["lead2reg_pct"] is None
