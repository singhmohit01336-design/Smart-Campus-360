import uuid
import pytest
from sqlalchemy import select

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import User


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "SmartCampus 360" in data["message"]


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_preflight(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_password_hashing():
    raw_pass = "SecurePass123!#"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "42", "role": "admin"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "42"
    assert decoded.get("role") == "admin"
    assert "exp" in decoded

    # Tampered token test
    tampered_token = token[:-4] + "fake"
    assert decode_access_token(tampered_token) is None


def test_login_invalid_credentials(client):
    payload = {
        "email": "nonexistent_user@example.com",
        "password": "WrongPassword123!",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_get_my_profile_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_my_profile_invalid_token(client):
    headers = {"Authorization": "Bearer invalid_or_tampered_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_registration_duplicate_and_login_flow(client, db_session):
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"student_{unique_id}@example.com"
    test_password = "TestPassword123!"
    test_name = f"Test Student {unique_id}"

    created_user_id = None
    try:
        # 1. Register new student
        register_payload = {
            "full_name": test_name,
            "email": test_email,
            "password": test_password,
        }
        reg_response = client.post("/auth/register", json=register_payload)
        assert reg_response.status_code == 201
        reg_data = reg_response.json()
        assert reg_data["email"] == test_email
        assert reg_data["full_name"] == test_name
        assert reg_data["role"] == "student"
        assert reg_data["is_active"] is True
        created_user_id = reg_data["id"]

        # 2. Try registering duplicate email -> Must return 409 Conflict
        dup_response = client.post("/auth/register", json=register_payload)
        assert dup_response.status_code == 409
        assert dup_response.json()["detail"] == "Email already registered"

        # 3. Login with credentials
        login_payload = {
            "email": test_email,
            "password": test_password,
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        access_token = token_data["access_token"]

        # 4. Access /auth/me with the token
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["id"] == created_user_id
        assert me_data["email"] == test_email
        assert me_data["full_name"] == test_name

    finally:
        # Clean up test user to preserve database state
        if created_user_id:
            user_to_delete = db_session.scalar(
                select(User).where(User.id == created_user_id)
            )
            if user_to_delete:
                db_session.delete(user_to_delete)
                db_session.commit()
