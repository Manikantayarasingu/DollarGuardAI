import uuid

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def unique_username():
    return f"test_admin_{uuid.uuid4().hex[:8]}"


def test_register_admin():
    username = unique_username()

    response = client.post(
        "/api/auth/register",
        params={
            "username": username,
            "password": "Test@12345",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == username
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True


def test_login_and_get_profile():
    username = unique_username()

    register_response = client.post(
        "/api/auth/register",
        params={
            "username": username,
            "password": "Test@12345",
            "role": "ADMIN",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    token = login_data["access_token"]

    profile_response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["username"] == username
    assert profile["role"] == "ADMIN"
    assert profile["is_active"] is True


def test_profile_requires_authentication():
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_admin_users_requires_authentication():
    response = client.get("/api/admin/users")

    assert response.status_code == 401


def test_admin_can_access_user_list():
    username = unique_username()

    client.post(
        "/api/auth/register",
        params={
            "username": username,
            "password": "Test@12345",
            "role": "ADMIN",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data
    assert data["count"] >= 1


def test_admin_can_access_audit_logs():
    username = unique_username()

    client.post(
        "/api/auth/register",
        params={
            "username": username,
            "password": "Test@12345",
            "role": "ADMIN",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/admin/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data