import uuid

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def unique_username(prefix="api_test_admin"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_admin():
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

    return username


def login(username):
    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    return data["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# BASIC API TESTS
# ============================================================

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"
    assert "application" in data
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert "application" in data
    assert "environment" in data


# ============================================================
# FINANCIAL API TESTS
# ============================================================

def test_summary_endpoint():
    response = client.get("/api/summary")

    assert response.status_code == 200

    data = response.json()

    required_fields = {
        "total_claims",
        "potential_leakage",
        "total_recovery_claims",
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
    }

    assert required_fields.issubset(data.keys())

    assert data["total_claims"] >= 0
    assert data["potential_leakage"] >= 0
    assert data["total_recovery_claims"] >= 0
    assert data["claimed_amount"] >= 0
    assert data["recovered_amount"] >= 0
    assert data["outstanding_amount"] >= 0


def test_claims_endpoint():
    response = client.get(
        "/api/claims",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["items"], list)

    assert len(data["items"]) <= 10


def test_recovery_endpoint():
    response = client.get(
        "/api/recovery",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["items"], list)

    assert len(data["items"]) <= 10


def test_vendor_endpoint():
    response = client.get(
        "/api/vendors",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["items"], list)

    assert len(data["items"]) <= 10


def test_investigations_endpoint():
    response = client.get(
        "/api/investigations",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["items"], list)


def test_investigation_packets_endpoint():
    response = client.get(
        "/api/investigation-packets",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["items"], list)


def test_anomalies_endpoint():
    response = client.get(
        "/api/anomalies",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["items"], list)


def test_contract_compliance_endpoint():
    response = client.get(
        "/api/contract-compliance",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["items"], list)


def test_recovery_analytics_endpoint():
    response = client.get(
        "/api/recovery-analytics"
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert isinstance(data["items"], list)


# ============================================================
# AUTHENTICATION FLOW
# ============================================================

def test_complete_authentication_flow():
    username = register_admin()

    token = login(username)

    response = client.get(
        "/api/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == username
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True


# ============================================================
# RBAC
# ============================================================

def test_admin_user_list():
    username = register_admin()

    token = login(username)

    response = client.get(
        "/api/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert data["count"] >= 1
    assert isinstance(data["items"], list)


def test_secure_recovery_requires_authentication():
    response = client.get(
        "/api/recovery/secure"
    )

    assert response.status_code == 401


def test_secure_recovery_admin_access():
    username = register_admin()

    token = login(username)

    response = client.get(
        "/api/recovery/secure",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data


def test_audit_logs_admin_access():
    username = register_admin()

    token = login(username)

    response = client.get(
        "/api/admin/audit-logs",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "items" in data

    assert data["count"] >= 1


# ============================================================
# AUTHENTICATION FAILURE TESTS
# ============================================================

def test_invalid_login():
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

    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_invalid_token():
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401