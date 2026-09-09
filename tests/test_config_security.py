import pytest

from app.config import Settings


def test_placeholder_secrets_allowed_in_development():
    settings = Settings(environment="development", jwt_secret_key="change-me-to-a-random-secret")
    settings.assert_secrets_configured()  # не должно бросать


def test_placeholder_secrets_rejected_outside_development():
    settings = Settings(
        environment="production",
        jwt_secret_key="change-me-to-a-random-secret",
        binolla_webhook_secret="a-sufficiently-long-real-secret-value",
        chatterfy_webhook_secret="a-sufficiently-long-real-secret-value",
        track_click_signing_secret="a-sufficiently-long-real-secret-value",
    )
    with pytest.raises(RuntimeError, match="jwt_secret_key"):
        settings.assert_secrets_configured()


def test_short_secret_rejected_outside_development():
    settings = Settings(
        environment="production",
        jwt_secret_key="short-secret-value-1234567890",
        binolla_webhook_secret="short",
        chatterfy_webhook_secret="a-sufficiently-long-real-secret-value",
        track_click_signing_secret="a-sufficiently-long-real-secret-value",
    )
    with pytest.raises(RuntimeError, match="binolla_webhook_secret"):
        settings.assert_secrets_configured()


def test_real_secrets_pass_outside_development():
    settings = Settings(
        environment="production",
        jwt_secret_key="a-sufficiently-long-real-secret-value",
        binolla_webhook_secret="a-sufficiently-long-real-secret-value",
        chatterfy_webhook_secret="a-sufficiently-long-real-secret-value",
        track_click_signing_secret="a-sufficiently-long-real-secret-value",
    )
    settings.assert_secrets_configured()  # не должно бросать
