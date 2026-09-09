import json
import uuid

from app.core.signing import compute_hmac_signature
from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user

TRACK_SECRET = "test-track-secret"


def _signed_click_kwargs(payload: dict) -> dict:
    body = json.dumps(payload).encode()
    signature = compute_hmac_signature(TRACK_SECRET, body)
    return {
        "content": body,
        "headers": {"Content-Type": "application/json", "X-Signature": signature},
    }


async def test_auto_assign_by_geo_on_click(client, db_session):
    manager = await make_user(
        db_session, UserRole.sales_manager, geo_coverage=["SY"], dialects=["levantine"]
    )

    resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": "aa-click-1", "geo": "SY"})
    )
    lead_id = resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.assigned_manager_id == manager.id


async def test_auto_assign_narrows_by_dialect(client, db_session):
    from app.models.enums import Dialect

    wrong_dialect_mgr = await make_user(
        db_session, UserRole.sales_manager, geo_coverage=["MA"], dialects=["gulf_najdi"]
    )
    right_dialect_mgr = await make_user(
        db_session, UserRole.sales_manager, geo_coverage=["MA"], dialects=["moroccan_darija"]
    )

    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post(
        "/api/v1/leads",
        json={"geo": "MA", "dialect": Dialect.moroccan_darija.value},
        headers=auth_headers(admin),
    )
    lead_id = resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.assigned_manager_id == right_dialect_mgr.id
    assert lead.assigned_manager_id != wrong_dialect_mgr.id


async def test_auto_assign_picks_least_loaded_manager(client, db_session):
    busy_mgr = await make_user(db_session, UserRole.sales_manager, geo_coverage=["SA"], dialects=[])
    free_mgr = await make_user(db_session, UserRole.sales_manager, geo_coverage=["SA"], dialects=[])

    admin = await make_user(db_session, UserRole.admin)

    # Догружаем busy_mgr тремя лидами вручную, прежде чем сработает auto-assign для нового.
    for _ in range(3):
        r = await client.post("/api/v1/leads", json={"geo": "SA"}, headers=auth_headers(admin))
        lid = r.json()["lead_id"]
        await client.post(
            f"/api/v1/leads/{lid}/assign", json={"manager_id": str(busy_mgr.id)}, headers=auth_headers(admin)
        )

    resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": "aa-click-load", "geo": "SA"})
    )
    lead_id = resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.assigned_manager_id == free_mgr.id


async def test_no_matching_manager_stays_unassigned(client, db_session):
    admin = await make_user(db_session, UserRole.admin)

    resp = await client.post(
        "/api/v1/track/click", **_signed_click_kwargs({"click_id": "aa-click-none", "geo": "SY"})
    )
    lead_id = resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.assigned_manager_id is None

    unassigned_resp = await client.get("/api/v1/leads?unassigned=true", headers=auth_headers(admin))
    assert unassigned_resp.status_code == 200
    ids = [item["lead_id"] for item in unassigned_resp.json()["items"]]
    assert lead_id in ids


async def test_unassigned_filter_forbidden_for_sales_manager(client, db_session):
    sm = await make_user(db_session, UserRole.sales_manager)
    resp = await client.get("/api/v1/leads?unassigned=true", headers=auth_headers(sm))
    assert resp.status_code == 403


async def test_patch_geo_retriggers_auto_assign(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    assert lead.assigned_manager_id is None

    manager = await make_user(db_session, UserRole.sales_manager, geo_coverage=["SY"], dialects=[])

    patch_resp = await client.patch(
        f"/api/v1/leads/{lead_id}", json={"geo": "SY"}, headers=auth_headers(admin)
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["assigned_manager_id"] == str(manager.id)
