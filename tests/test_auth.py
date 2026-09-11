from app.models.enums import UserRole
from tests.conftest import make_user


async def test_login_without_2fa_returns_setup_scoped_token(client, db_session):
    await make_user(db_session, UserRole.admin, email="admin@example.com", password="secret123")
    # admin без включённой 2FA получает ограниченный bootstrap-токен, а не 403 -
    # иначе 2FA невозможно было бы включить в принципе (курица и яйцо).
    resp = await client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    assert resp.status_code == 200
    setup_token = resp.json()["access_token"]

    # Этим токеном нельзя дёрнуть обычный защищённый эндпоинт.
    forbidden_resp = await client.get(
        "/api/v1/leads", headers={"Authorization": f"Bearer {setup_token}"}
    )
    assert forbidden_resp.status_code == 403


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


async def test_2fa_setup_and_enable_write_audit_log(client, db_session):
    import pyotp
    from sqlalchemy import select

    from app.models.audit_log import AuditLog
    from tests.conftest import auth_headers

    user = await make_user(db_session, UserRole.admin, email="admin4@example.com", password="secret123")

    setup_resp = await client.post("/api/v1/auth/2fa/setup", headers=auth_headers(user))
    secret = setup_resp.json()["secret"]
    await client.post(
        "/api/v1/auth/2fa/verify", json={"code": pyotp.TOTP(secret).now()}, headers=auth_headers(user)
    )

    result = await db_session.execute(select(AuditLog).where(AuditLog.entity_id == str(user.id)))
    actions = {log.action for log in result.scalars().all()}
    assert "2fa_setup_started" in actions
    assert "2fa_enabled" in actions


async def test_admin_full_bootstrap_flow_via_real_login_only(client, db_session):
    """Полный путь ровно так, как это сделал бы реальный пользователь через
    отдельные HTTP-запросы (без обхода через auth_headers) - проверяет, что
    изменения из /2fa/setup и /2fa/verify реально коммитятся в БД."""
    import pyotp

    await make_user(db_session, UserRole.admin, email="admin3@example.com", password="secret123")

    bootstrap_resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin3@example.com", "password": "secret123"}
    )
    setup_token = bootstrap_resp.json()["access_token"]
    setup_headers = {"Authorization": f"Bearer {setup_token}"}

    setup_resp = await client.post("/api/v1/auth/2fa/setup", headers=setup_headers)
    secret = setup_resp.json()["secret"]

    verify_resp = await client.post(
        "/api/v1/auth/2fa/verify", json={"code": pyotp.TOTP(secret).now()}, headers=setup_headers
    )
    assert verify_resp.status_code == 204

    final_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin3@example.com", "password": "secret123", "totp_code": pyotp.TOTP(secret).now()},
    )
    assert final_login.status_code == 200
    full_token = final_login.json()["access_token"]

    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {full_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "admin3@example.com"


async def test_change_password_success_and_relogin(client, db_session):
    from tests.conftest import auth_headers

    user = await make_user(db_session, UserRole.sales_manager, email="pwtest@example.com", password="oldpass123")

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "oldpass123", "new_password": "newpass456"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login", json={"email": "pwtest@example.com", "password": "oldpass123"}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login", json={"email": "pwtest@example.com", "password": "newpass456"}
    )
    assert new_login.status_code == 200


async def test_change_password_wrong_current_rejected(client, db_session):
    from tests.conftest import auth_headers

    user = await make_user(db_session, UserRole.sales_manager, email="pwtest2@example.com", password="oldpass123")

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "newpass456"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 401
