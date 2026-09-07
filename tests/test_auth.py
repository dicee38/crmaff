from app.models.enums import UserRole
from tests.conftest import make_user


async def test_login_success(client, db_session):
    user = await make_user(db_session, UserRole.admin, email="admin@example.com", password="secret123")
    # admin требует 2FA - без него логин должен быть запрещён.
    resp = await client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    assert resp.status_code == 403


async def test_login_non_admin_no_2fa_required(client, db_session):
    await make_user(db_session, UserRole.sales_manager, email="sm@example.com", password="secret123")
    resp = await client.post("/api/v1/auth/login", json={"email": "sm@example.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client, db_session):
    await make_user(db_session, UserRole.sales_manager, email="sm2@example.com", password="secret123")
    resp = await client.post("/api/v1/auth/login", json={"email": "sm2@example.com", "password": "wrong"})
    assert resp.status_code == 401


async def test_admin_2fa_setup_and_login(client, db_session):
    import pyotp

    user = await make_user(db_session, UserRole.admin, email="admin2@example.com", password="secret123")
    from tests.conftest import auth_headers

    setup_resp = await client.post("/api/v1/auth/2fa/setup", headers=auth_headers(user))
    assert setup_resp.status_code == 200
    secret = setup_resp.json()["secret"]

    code = pyotp.TOTP(secret).now()
    verify_resp = await client.post("/api/v1/auth/2fa/verify", json={"code": code}, headers=auth_headers(user))
    assert verify_resp.status_code == 204

    login_code = pyotp.TOTP(secret).now()
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin2@example.com", "password": "secret123", "totp_code": login_code},
    )
    assert login_resp.status_code == 200
