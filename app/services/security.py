import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-development-secret-key-before-production",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(
    subject: str,
    role: str,
    expires_minutes: Optional[int] = None,
) -> str:
    minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    payload = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired access token.") from exc
