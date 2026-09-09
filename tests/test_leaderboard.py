import json

from app.core.signing import compute_hmac_signature
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


async def _manager_with_ftd(client, db_session, admin, click_id: str, payout: str) -> "object":
    manager = await make_user(db_session, UserRole.sales_manager, geo_coverage=["SY"], dialects=[])
    click_resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": click_id, "geo": "SY"})
    )
    lead_id = click_resp.json()["lead_id"]
    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(manager.id)}, headers=auth_headers(admin)
    )
    await client.get(_binolla_url(status="reg", eid=f"{click_id}-reg", cid=click_id))
    await client.get(_binolla_url(status="ftd", eid=f"{click_id}-ftd", cid=click_id, payout=payout))
    return manager


async def test_leaderboard_ranks_by_cashflow_descending(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    top_manager = await _manager_with_ftd(client, db_session, admin, "lb-click-top", "500")
    low_manager = await _manager_with_ftd(client, db_session, admin, "lb-click-low", "10")

    resp = await client.get(
        "/api/v1/leaderboard?metric=cashflow&period=month", headers=auth_headers(top_manager)
    )
    assert resp.status_code == 200
    body = resp.json()
    ranks_by_manager = {row["manager_id"]: row["rank"] for row in body["rows"]}
    assert ranks_by_manager[str(top_manager.id)] < ranks_by_manager[str(low_manager.id)]

    top_row = next(r for r in body["rows"] if r["manager_id"] == str(top_manager.id))
    assert top_row["is_current_user"] is True
    assert float(top_row["value"]) == 500.0


async def test_leaderboard_current_user_delta(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    first = await _manager_with_ftd(client, db_session, admin, "lb-delta-1", "300")
    second = await _manager_with_ftd(client, db_session, admin, "lb-delta-2", "100")

    resp = await client.get(
        "/api/v1/leaderboard?metric=cashflow&period=month", headers=auth_headers(second)
    )
    body = resp.json()
    assert body["current_user_rank"] == 2
    assert float(body["delta_to_rank_above"]) == 200.0
    assert body["delta_over_rank_below"] is None or float(body["delta_over_rank_below"]) == 100.0


async def test_leaderboard_accessible_to_all_roles(client, db_session):
    for role in (UserRole.compliance, UserRole.analyst, UserRole.smm_manager, UserRole.tech_lead):
        user = await make_user(db_session, role)
        resp = await client.get("/api/v1/leaderboard", headers=auth_headers(user))
        assert resp.status_code == 200, f"role={role} got {resp.status_code}"


async def test_leaderboard_lead_to_fd_metric(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    manager = await _manager_with_ftd(client, db_session, admin, "lb-l2fd", "20")

    resp = await client.get(
        "/api/v1/leaderboard?metric=lead_to_fd&period=month", headers=auth_headers(manager)
    )
    assert resp.status_code == 200
    row = next(r for r in resp.json()["rows"] if r["manager_id"] == str(manager.id))
    assert float(row["value"]) == 100.0  # 1 лид, 1 ftd -> 100%


async def test_leaderboard_invalid_metric_rejected(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.get("/api/v1/leaderboard?metric=bogus", headers=auth_headers(admin))
    assert resp.status_code == 422
