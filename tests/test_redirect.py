import uuid

from app.models.enums import CommissionModel, OfferStatus
from app.models.offer import Offer


_DEFAULT_TEMPLATE = "https://binolla.com/?lid=28941&click_id={click_id}&site_id=1"


async def _create_offer(
    db_session, *, status: OfferStatus = OfferStatus.active, template: str | None = _DEFAULT_TEMPLATE
) -> Offer:
    offer = Offer(
        id=uuid.uuid4(),
        partner_name="Binolla",
        geo="SY",
        commission_model=CommissionModel.cpa,
        status=status,
        redirect_url_template=template,
    )
    db_session.add(offer)
    await db_session.commit()
    return offer


async def test_redirect_creates_lead_and_redirects_with_click_id(client, db_session):
    offer = await _create_offer(db_session)

    resp = await client.get(f"/api/v1/go/{offer.id}?campaign_id=camp-1&geo=SY")
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "binolla.com" in location
    assert "click_id=" in location
    assert "site_id=1" in location


async def test_redirect_creates_tracking_event(client, db_session):
    offer = await _create_offer(db_session)

    resp = await client.get(f"/api/v1/go/{offer.id}?campaign_id=camp-2")
    location = resp.headers["location"]
    click_id = location.split("click_id=")[1].split("&")[0]

    from sqlalchemy import select

    from app.models.tracking_event import TrackingEvent

    result = await db_session.execute(select(TrackingEvent).where(TrackingEvent.click_id == click_id))
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.campaign_id == "camp-2"
    assert event.lead_id is not None


async def test_redirect_missing_offer_404(client):
    resp = await client.get(f"/api/v1/go/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_redirect_paused_offer_404(client, db_session):
    offer = await _create_offer(db_session, status=OfferStatus.paused)
    resp = await client.get(f"/api/v1/go/{offer.id}")
    assert resp.status_code == 404


async def test_redirect_offer_without_template_409(client, db_session):
    offer = await _create_offer(db_session, template=None)
    resp = await client.get(f"/api/v1/go/{offer.id}")
    assert resp.status_code == 409


async def test_redirect_generates_unique_click_id_each_time(client, db_session):
    offer = await _create_offer(db_session)

    resp1 = await client.get(f"/api/v1/go/{offer.id}")
    resp2 = await client.get(f"/api/v1/go/{offer.id}")

    click_id_1 = resp1.headers["location"].split("click_id=")[1].split("&")[0]
    click_id_2 = resp2.headers["location"].split("click_id=")[1].split("&")[0]
    assert click_id_1 != click_id_2
