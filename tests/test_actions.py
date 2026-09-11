from app.models.enums import UserRole
from tests.conftest import auth_headers, make_user


async def test_manual_action_matches_lead_by_click_id(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    import uuid

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.external_click_id = "manual-click-1"
    await db_session.commit()

    resp = await client.post(
        "/api/v1/actions",
        json={
            "player_id": "manual-click-1",
            "partner_name": "Binolla",
            "channel": "MENA-KARIM",
            "event_type": "ftd",
            "amount": "100.00",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["lead_id"] == lead_id
    assert body["source"] == "manual"
    assert body["entered_by"] == str(admin.id)
    assert body["channel"] == "MENA-KARIM"
    assert body["validation_flags"] is None


async def test_manual_action_amount_required_for_ftd(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post(
        "/api/v1/actions",
        json={"player_id": "no-such-player", "partner_name": "Binolla", "event_type": "ftd"},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 400


async def test_manual_action_registration_no_amount_required(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post(
        "/api/v1/actions",
        json={"player_id": "no-such-player-2", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201


async def test_manual_action_unmatched_lead_not_blocked(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    resp = await client.post(
        "/api/v1/actions",
        json={
            "player_id": "totally-unknown-player",
            "partner_name": "Binolla",
            "event_type": "registration",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["lead_id"] is None
    assert body["validation_flags"] == {"unmatched_lead": True}


async def test_manual_action_possible_duplicate_flagged_not_blocked(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]

    import uuid

    from app.crud.lead import get_lead

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.external_click_id = "dup-click-1"
    await db_session.commit()

    payload = {
        "player_id": "dup-click-1",
        "partner_name": "Binolla",
        "event_type": "deposit",
        "amount": "50.00",
    }
    resp1 = await client.post("/api/v1/actions", json=payload, headers=auth_headers(admin))
    resp2 = await client.post("/api/v1/actions", json=payload, headers=auth_headers(admin))
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["validation_flags"] is None
    assert resp2.json()["validation_flags"] == {"possible_duplicate": True}


async def test_analyst_cannot_create_action(client, db_session):
    analyst = await make_user(db_session, UserRole.analyst)
    resp = await client.post(
        "/api/v1/actions",
        json={"player_id": "x", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(analyst),
    )
    assert resp.status_code == 403


async def test_analyst_can_view_all_actions(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    analyst = await make_user(db_session, UserRole.analyst)

    await client.post(
        "/api/v1/actions",
        json={"player_id": "y", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )

    resp = await client.get("/api/v1/actions", headers=auth_headers(analyst))
    assert resp.status_code == 200
    body = resp.json()
    assert body["aggregates"]["total_actions"] == 1


async def test_sales_manager_sees_only_own_actions(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    sm1 = await make_user(db_session, UserRole.sales_manager)
    sm2 = await make_user(db_session, UserRole.sales_manager)

    lead1_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead1_id = lead1_resp.json()["lead_id"]
    await client.post(
        f"/api/v1/leads/{lead1_id}/assign", json={"manager_id": str(sm1.id)}, headers=auth_headers(admin)
    )

    import uuid

    from app.crud.lead import get_lead

    lead1 = await get_lead(db_session, uuid.UUID(lead1_id))
    lead1.external_click_id = "sm-scope-click"
    await db_session.commit()

    await client.post(
        "/api/v1/actions",
        json={"player_id": "sm-scope-click", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )

    resp_sm1 = await client.get("/api/v1/actions", headers=auth_headers(sm1))
    assert resp_sm1.status_code == 200
    assert resp_sm1.json()["aggregates"]["total_actions"] == 1

    resp_sm2 = await client.get("/api/v1/actions", headers=auth_headers(sm2))
    assert resp_sm2.status_code == 200
    assert resp_sm2.json()["aggregates"]["total_actions"] == 0


async def test_compliance_cannot_view_actions(client, db_session):
    compliance = await make_user(db_session, UserRole.compliance)
    resp = await client.get("/api/v1/actions", headers=auth_headers(compliance))
    assert resp.status_code == 403


async def test_actions_list_row_has_player_id_and_manager(client, db_session):
    import uuid

    from app.crud.lead import get_lead

    admin = await make_user(db_session, UserRole.admin)
    sm = await make_user(db_session, UserRole.sales_manager, full_name="Иван Демидов")

    lead_resp = await client.post("/api/v1/leads", json={"geo": "SY"}, headers=auth_headers(admin))
    lead_id = lead_resp.json()["lead_id"]
    await client.post(
        f"/api/v1/leads/{lead_id}/assign", json={"manager_id": str(sm.id)}, headers=auth_headers(admin)
    )

    lead = await get_lead(db_session, uuid.UUID(lead_id))
    lead.external_click_id = "row-check-click"
    await db_session.commit()

    await client.post(
        "/api/v1/actions",
        json={
            "player_id": "row-check-click",
            "partner_name": "PocketOption",
            "channel": "MENA-Kamil",
            "event_type": "ftd",
            "amount": "52.17",
        },
        headers=auth_headers(admin),
    )

    resp = await client.get("/api/v1/actions", headers=auth_headers(admin))
    assert resp.status_code == 200
    row = resp.json()["items"][0]
    assert row["player_external_id"] == "row-check-click"
    assert row["manager_full_name"] == "Иван Демидов"
    assert row["manager_role"] == "sales_manager"
    assert row["partner"] == "PocketOption"
    assert row["channel"] == "MENA-Kamil"
    assert float(row["amount"]) == 52.17
    assert row["lead_id"] == lead_id


async def test_actions_list_row_unmatched_lead_has_no_manager(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    await client.post(
        "/api/v1/actions",
        json={"player_id": "no-lead-for-this-one", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )

    resp = await client.get("/api/v1/actions", headers=auth_headers(admin))
    row = resp.json()["items"][0]
    assert row["lead_id"] is None
    assert row["manager_full_name"] is None
    assert row["player_external_id"] == "no-lead-for-this-one"


async def test_actions_deposit_aggregates(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    await client.post(
        "/api/v1/actions",
        json={"player_id": "agg-1", "partner_name": "Binolla", "event_type": "ftd", "amount": "100"},
        headers=auth_headers(admin),
    )
    await client.post(
        "/api/v1/actions",
        json={"player_id": "agg-2", "partner_name": "Binolla", "event_type": "deposit", "amount": "50"},
        headers=auth_headers(admin),
    )
    await client.post(
        "/api/v1/actions",
        json={"player_id": "agg-3", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )

    resp = await client.get("/api/v1/actions", headers=auth_headers(admin))
    aggregates = resp.json()["aggregates"]
    assert aggregates["total_actions"] == 3
    assert aggregates["deposit_count"] == 2
    assert float(aggregates["deposit_sum"]) == 150.0


async def test_admin_can_delete_action(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    create_resp = await client.post(
        "/api/v1/actions",
        json={"player_id": "del-1", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )
    event_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/actions/{event_id}", headers=auth_headers(admin))
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/actions", headers=auth_headers(admin))
    assert all(item["id"] != event_id for item in list_resp.json()["items"])


async def test_non_admin_cannot_delete_action(client, db_session):
    admin = await make_user(db_session, UserRole.admin)
    mop_lead = await make_user(db_session, UserRole.mop_lead)
    create_resp = await client.post(
        "/api/v1/actions",
        json={"player_id": "del-2", "partner_name": "Binolla", "event_type": "registration"},
        headers=auth_headers(admin),
    )
    event_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/actions/{event_id}", headers=auth_headers(mop_lead))
    assert resp.status_code == 403


async def test_delete_nonexistent_action_404(client, db_session):
    import uuid

    admin = await make_user(db_session, UserRole.admin)
    resp = await client.delete(f"/api/v1/actions/{uuid.uuid4()}", headers=auth_headers(admin))
    assert resp.status_code == 404
