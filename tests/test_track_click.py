import json

from app.core.signing import compute_hmac_signature

SECRET = "test-track-secret"


def _signed_post_kwargs(payload: dict) -> dict:
    body = json.dumps(payload).encode()
    signature = compute_hmac_signature(SECRET, body)
    return {
        "content": body,
        "headers": {"Content-Type": "application/json", "X-Signature": signature},
    }


async def test_track_click_creates_lead_and_event(client):
    payload = {"click_id": "click-abc-123", "geo": "SY", "campaign_id": "camp-1"}
    resp = await client.post("/api/v1/track/click", **_signed_post_kwargs(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["click_id"] == "click-abc-123"
    assert data["lead_id"]


async def test_track_click_invalid_signature_rejected(client):
    payload = {"click_id": "click-bad-sig"}
    body = json.dumps(payload).encode()
    resp = await client.post(
        "/api/v1/track/click",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": "deadbeef"},
    )
    assert resp.status_code == 401


async def test_track_click_idempotent_same_click_id(client):
    payload = {"click_id": "click-dup-1", "geo": "MA"}
    resp1 = await client.post("/api/v1/track/click", **_signed_post_kwargs(payload))
    resp2 = await client.post("/api/v1/track/click", **_signed_post_kwargs(payload))
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["lead_id"] == resp2.json()["lead_id"]
    assert resp1.json()["tracking_event_id"] == resp2.json()["tracking_event_id"]


async def test_track_click_does_not_duplicate_lead_for_same_telegram_user(client):
    payload1 = {"click_id": "click-tg-1", "telegram_user_id": "tg-999", "geo": "SA"}
    payload2 = {"click_id": "click-tg-2", "telegram_user_id": "tg-999", "geo": "SA"}
    resp1 = await client.post("/api/v1/track/click", **_signed_post_kwargs(payload1))
    resp2 = await client.post("/api/v1/track/click", **_signed_post_kwargs(payload2))
    assert resp1.json()["lead_id"] == resp2.json()["lead_id"]
