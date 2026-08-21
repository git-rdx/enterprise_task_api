from sqlalchemy import select

import app.services.auth_service as auth_service_module
from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User


def test_login_success(client, verified_user):

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, verified_user):

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "WrongPassword123!"},
    )

    assert response.status_code == 401


def test_login_user_not_found(client):

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "SomePassword123!"},
    )

    assert response.status_code == 401


def test_login_unverified_user(client, unverified_user):

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "TestPassword123!"},
    )

    assert response.status_code == 403


def test_current_user_authenticated(client, auth_headers):

    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200


def test_current_user_without_token(client):

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_register_user(client, db, monkeypatch):

    # Prevent real Celery task
    monkeypatch.setattr(
        auth_service_module.send_verification_email,
        "delay",
        lambda *args, **kwargs: None,
    )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "New Test User",
            "email": "newuser@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    user = db.query(User).filter(User.email == "newuser@example.com").first()

    assert user is not None
    assert user.is_verified is False
    assert user.password_hash != "TestPassword123!"


def test_refresh_token_rotation(client, verified_user, db):

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    assert login_response.status_code == 200

    first_refresh_token = login_response.json()["refresh_token"]

    # Rotate refresh token
    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first_refresh_token}
    )

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access_token" in data
    assert "refresh_token" in data

    second_refresh_token = data["refresh_token"]

    assert second_refresh_token != first_refresh_token

    old_token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(first_refresh_token)
        )
    )

    new_token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(second_refresh_token)
        )
    )

    assert old_token_record is not None
    assert new_token_record is not None

    assert old_token_record.revoked_at is not None

    assert old_token_record.replaced_by == new_token_record.id

    assert old_token_record.family_id == new_token_record.family_id


def test_refresh_token_reuse_detection(client, verified_user):

    # --------------------------
    # Login → R1
    # --------------------------

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    assert login_response.status_code == 200

    refresh_token_1 = login_response.json()["refresh_token"]

    # --------------------------
    # R1 → R2
    # --------------------------

    first_refresh = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token_1}
    )

    assert first_refresh.status_code == 200

    refresh_token_2 = first_refresh.json()["refresh_token"]

    # --------------------------
    # Reuse old R1
    # --------------------------

    reuse_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token_1}
    )

    assert reuse_response.status_code == 401

    # --------------------------
    # R2 should now also fail
    # because family was revoked
    # --------------------------

    family_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token_2}
    )

    assert family_response.status_code == 401
