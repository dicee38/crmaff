import json

from app.core.signing import compute_hmac_signature

SECRET = "test-chatterfy-secret"


def _signed_post_kwargs(payload: dict) -> dict:
    body = json.dumps(payload).encode()
    signature = compute_hmac_signature(SECRET, body)
    return {
        "content": body,
        "headers": {"Content-Type": "application/json", "X-Signature": signature},
    }


async def test_chatterfy_webhook_creates_lead_and_communication(client):
    payload = {
        "external_message_id": "msg-1",
        "telegram_user_id": "tg-1001",
        "message_text": "Hello, I want to trade",
    }
    resp = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload))
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead_id"]
    assert body["communication_id"]


async def test_chatterfy_webhook_invalid_signature_rejected(client):
    payload = {"external_message_id": "msg-bad", "telegram_user_id": "tg-2"}
    body = json.dumps(payload).encode()
    resp = await client.post(
        "/api/v1/webhooks/chatterfy",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": "deadbeef"},
    )
    assert resp.status_code == 401


async def test_chatterfy_webhook_idempotent_same_external_message_id(client):
    payload = {"external_message_id": "msg-dup-1", "telegram_user_id": "tg-1002", "message_text": "hi"}
    resp1 = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload))
    resp2 = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload))
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["lead_id"] == resp2.json()["lead_id"]
    assert resp1.json()["communication_id"] == resp2.json()["communication_id"]


async def test_chatterfy_webhook_does_not_duplicate_lead_for_same_telegram_user(client):
    payload1 = {"external_message_id": "msg-a", "telegram_user_id": "tg-1003", "message_text": "one"}
    payload2 = {"external_message_id": "msg-b", "telegram_user_id": "tg-1003", "message_text": "two"}
    resp1 = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload1))
    resp2 = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload2))
    assert resp1.json()["lead_id"] == resp2.json()["lead_id"]


async def test_chatterfy_webhook_matches_lead_by_click_id_start_param(client):
    from app.core.signing import compute_hmac_signature as track_sig

    track_payload = {"click_id": "click-for-tg-match"}
    track_body = json.dumps(track_payload).encode()
    track_signature = track_sig("test-track-secret", track_body)
    track_resp = await client.post(
        "/api/v1/track/click",
        content=track_body,
        headers={"Content-Type": "application/json", "X-Signature": track_signature},
    )
    click_lead_id = track_resp.json()["lead_id"]

    message_payload = {
        "external_message_id": "msg-matched",
        "telegram_user_id": "tg-matched-1",
        "start_param": "click-for-tg-match",
    }
    resp = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(message_payload))
    assert resp.json()["lead_id"] == click_lead_id


async def test_chatterfy_webhook_new_lead_status_becomes_contacted(client, db_session):
    import uuid

    from app.models.lead import Lead

    payload = {"external_message_id": "msg-status-1", "telegram_user_id": "tg-status-1", "message_text": "hi"}
    resp = await client.post("/api/v1/webhooks/chatterfy", **_signed_post_kwargs(payload))
    lead_id = resp.json()["lead_id"]

    lead = await db_session.get(Lead, uuid.UUID(lead_id))
    assert lead.status.value == "contacted"
