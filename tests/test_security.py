from app.services.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "Test@12345"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword", password_hash)


def test_jwt_token():
    token = create_access_token(
        subject="test_admin",
        role="ADMIN",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "test_admin"
    assert payload["role"] == "ADMIN"
    assert "exp" in payload