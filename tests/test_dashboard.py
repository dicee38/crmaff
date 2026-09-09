import json
import uuid

from app.core.signing import compute_hmac_signature
from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user

TRACK_SECRET = "test-track-secret"
BINOLLA_SECRET = "test-binolla-secret"


def _signed_click_kwargs(payload: dict) -> dict:
    body = json.dumps(payload).encode()
    signature = compute_hmac_signature(TRACK_SECRET, body)
    return {"content": body, "headers": {"Content-Type": "application/json", "X-Signature": signature}}


async def _binolla_url(**params) -> str:
    params.setdefault("secret", BINOLLA_SECRET)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/api/v1/webhooks/binolla?{query}"


async def test_funnel_counts_full_chain(client, db_session):
    admin = await make_user(db_session, UserRole.admin)

    click_resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": "dash-click-1", "geo": "SY"})
    )
    lead_id = click_resp.json()["lead_id"]

    await client.get(await _binolla_url(status="reg", eid="dash-evt-1", cid="dash-click-1"))
    await client.get(await _binolla_url(status="ftd", eid="dash-evt-2", cid="dash-click-1", payout="100"))

    resp = await client.get("/api/v1/dashboard/funnel", headers=auth_headers(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert body["clicks"] >= 1
    assert body["leads_created"] >= 1
    assert body["registered"] >= 1
    assert body["ftd"] >= 1
    assert float(body["commission_total"]) >= 100.0


async def test_kpi_conversion_rates(client, db_session):
    admin = await make_user(db_session, UserRole.admin)

    for i in range(4):
        await client.post(
            "/api/v1/track/click", **_signed_click_kwargs({"click_id": f"kpi-click-{i}", "geo": "MA"})
        )

    # Из 4 лидов - 2 регистрации, из них 1 FTD.
    await client.get(await _binolla_url(status="reg", eid="kpi-evt-1", cid="kpi-click-0"))
    await client.get(await _binolla_url(status="reg", eid="kpi-evt-2", cid="kpi-click-1"))
    await client.get(await _binolla_url(status="ftd", eid="kpi-evt-3", cid="kpi-click-0", payout="50"))

    resp = await client.get("/api/v1/dashboard/kpi?geo=MA", headers=auth_headers(admin))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_leads"] == 4
    assert body["total_registered"] == 2
    assert body["total_ftd"] == 1
    assert body["lead2reg_pct"] == 50.0
    assert body["reg2fd_pct"] == 50.0


async def test_dashboard_forbidden_for_sales_manager(client, db_session):
    sm = await make_user(db_session, UserRole.sales_manager)
    resp = await client.get("/api/v1/dashboard/funnel", headers=auth_headers(sm))
    assert resp.status_code == 403


async def test_dashboard_allowed_for_analyst(client, db_session):
    analyst = await make_user(db_session, UserRole.analyst)
    resp = await client.get("/api/v1/dashboard/kpi", headers=auth_headers(analyst))
    assert resp.status_code == 200
