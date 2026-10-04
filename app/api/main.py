"""
DollarGuard AI
FastAPI Backend

Features:
- Health and system endpoints
- Financial summary
- Leakage claims
- Recovery claims
- Vendor analytics
- AI investigations
- Investigation packets
- ML anomalies
- Contract compliance
- Recovery analytics
- JWT authentication
- Role-based access control
- Audit logging
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.health import get_health_status
from app.database.connection import Base, SessionLocal, engine, get_db
from app.database.init_db import initialize_database
from app.models.audit import AuditLog
from app.models.claim import Claim
from app.models.system import SystemInfo
from app.models.user import User
from app.services.audit import write_audit_log
from app.services.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="DollarGuard AI API",
    description=(
        "AI-powered revenue leakage detection, investigation, "
        "contract compliance, and recovery management platform."
    ),
    version="0.2.0",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

CLAIMS_FILE = PROCESSED_DIR / "unified_claims.csv"
RECOVERY_FILE = PROCESSED_DIR / "recovery_claims.csv"
VENDOR_FILE = PROCESSED_DIR / "vendor_analytics.csv"
INVESTIGATIONS_FILE = PROCESSED_DIR / "investigation_reports.csv"
PACKETS_FILE = PROCESSED_DIR / "investigation_packets.csv"
ANOMALIES_FILE = PROCESSED_DIR / "ml_anomalies.csv"
CONTRACT_COMPLIANCE_FILE = (
    PROCESSED_DIR / "contract_compliance.csv"
)
RECOVERY_ANALYTICS_FILE = (
    PROCESSED_DIR / "recovery_analytics.csv"
)


# ============================================================
# AUTHENTICATION
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


# Supported application roles.
ALLOWED_ROLES = {
    "ADMIN",
    "ANALYST",
    "INVESTIGATOR",
    "RECOVERY_MANAGER",
    "VIEWER",
}


# ============================================================
# DATA HELPERS
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """
    Safely load a CSV file.

    Returns an empty DataFrame when the file does not exist
    or cannot be read.
    """

    if not path.exists():
        return pd.DataFrame()

    try:
        dataframe = pd.read_csv(path)

        dataframe.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in dataframe.columns
        ]

        return dataframe

    except Exception:
        return pd.DataFrame()


def clean_records(
    dataframe: pd.DataFrame,
    limit: int = 100,
):
    """
    Convert a DataFrame to JSON-safe Python records.

    Pandas may contain NaN, +Infinity, or -Infinity values.
    Standard JSON does not allow those values, so they are
    converted to None before returning API responses.
    """

    if dataframe is None or dataframe.empty:
        return []

    result = dataframe.head(limit).copy()

    # Replace infinite numeric values with NaN.
    result = result.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # Convert missing values to Python None.
    result = result.astype(object)

    result = result.where(
        pd.notna(result),
        None,
    )

    return result.to_dict(
        orient="records"
    )


def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        number = float(value)

        if pd.isna(number):
            return default

        if number in (
            float("inf"),
            float("-inf"),
        ):
            return default

        return number

    except (
        ValueError,
        TypeError,
    ):
        return default


# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Decode JWT token and return the active user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = decode_access_token(token)

        username = payload.get("sub")

        if not username:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


def require_roles(*allowed_roles):
    """
    FastAPI dependency factory for role-based access control.
    """

    normalized_roles = {
        role.upper()
        for role in allowed_roles
    }

    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
    ):
        if current_user.role.upper() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "status": "running",
        "message": "DollarGuard AI API is running.",
        "version": "0.2.0",
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return get_health_status()


# ============================================================
# SUMMARY
# ============================================================

@app.get("/api/summary")
def get_summary():

    claims = load_csv(
        CLAIMS_FILE
    )

    recovery = load_csv(
        RECOVERY_FILE
    )

    potential_leakage = 0.0

    if (
        not claims.empty
        and "potential_leakage" in claims.columns
    ):
        potential_leakage = float(
            pd.to_numeric(
                claims["potential_leakage"],
                errors="coerce",
            )
            .fillna(0)
            .replace(
                [
                    float("inf"),
                    float("-inf"),
                ],
                0,
            )
            .sum()
        )

    claimed_amount = 0.0
    recovered_amount = 0.0
    outstanding_amount = 0.0

    if not recovery.empty:

        if "claimed_amount" in recovery.columns:
            claimed_amount = float(
                pd.to_numeric(
                    recovery["claimed_amount"],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )

        if "recovered_amount" in recovery.columns:
            recovered_amount = float(
                pd.to_numeric(
                    recovery["recovered_amount"],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )

        if "outstanding_amount" in recovery.columns:
            outstanding_amount = float(
                pd.to_numeric(
                    recovery["outstanding_amount"],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )

    recovery_rate = (
        recovered_amount
        / claimed_amount
        * 100
        if claimed_amount > 0
        else 0.0
    )

    return {
        "total_claims": int(
            len(claims)
        ),
        "claims_detected": int(
            len(claims)
        ),
        "potential_leakage": potential_leakage,
        "total_recovery_claims": int(
            len(recovery)
        ),
        "investigations": int(
            len(load_csv(INVESTIGATIONS_FILE))
        ),
        "vendors_analyzed": int(
            len(load_csv(VENDOR_FILE))
        ),
        "claimed_amount": claimed_amount,
        "recovered_amount": recovered_amount,
        "outstanding_amount": outstanding_amount,
        "recovery_rate": recovery_rate,
    }


# ============================================================
# CLAIMS
# ============================================================

@app.get("/api/claims")
def get_claims(
    leakage_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status_filter: Optional[str] = None,
    vendor_id: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        CLAIMS_FILE
    )

    if dataframe.empty:
        return {
            "count": 0,
            "items": [],
        }

    if (
        leakage_type
        and "leakage_type" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["leakage_type"]
            .astype(str)
            .str.upper()
            == leakage_type.upper()
        ]

    if (
        risk_level
        and "risk_level" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["risk_level"]
            .astype(str)
            .str.upper()
            == risk_level.upper()
        ]

    if (
        status_filter
        and "status" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["status"]
            .astype(str)
            .str.upper()
            == status_filter.upper()
        ]

    if (
        vendor_id
        and "vendor_id" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["vendor_id"]
            .astype(str)
            .str.upper()
            == vendor_id.upper()
        ]

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# SINGLE CLAIM
# ============================================================

@app.get("/api/claims/{claim_id}")
def get_claim(
    claim_id: str,
):

    dataframe = load_csv(
        CLAIMS_FILE
    )

    if dataframe.empty:
        raise HTTPException(
            status_code=404,
            detail="Claim data not found.",
        )

    if "claim_id" not in dataframe.columns:
        raise HTTPException(
            status_code=404,
            detail="Claim ID column not found.",
        )

    matches = dataframe[
        dataframe["claim_id"]
        .astype(str)
        == claim_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Claim not found.",
        )

    return matches.iloc[0].to_dict()


# ============================================================
# RECOVERY
# ============================================================

@app.get("/api/recovery")
def get_recovery(
    claim_status: Optional[str] = None,
    recovery_priority: Optional[str] = None,
    vendor_id: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        RECOVERY_FILE
    )

    if dataframe.empty:
        return {
            "count": 0,
            "items": [],
        }

    if (
        claim_status
        and "claim_status" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["claim_status"]
            .astype(str)
            .str.upper()
            == claim_status.upper()
        ]

    if (
        recovery_priority
        and "recovery_priority" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["recovery_priority"]
            .astype(str)
            .str.upper()
            == recovery_priority.upper()
        ]

    if (
        vendor_id
        and "vendor_id" in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["vendor_id"]
            .astype(str)
            .str.upper()
            == vendor_id.upper()
        ]

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# SECURE RECOVERY
#
# IMPORTANT:
# This route must appear BEFORE
# /api/recovery/{recovery_claim_id}
# so "secure" is not interpreted as a claim ID.
# ============================================================

@app.get("/api/recovery/secure")
def secure_recovery_view(
    current_user: User = Depends(
        require_roles(
            "ADMIN",
            "ANALYST",
            "RECOVERY_MANAGER",
        )
    ),
    db: Session = Depends(get_db),
):

    recovery = load_csv(
        RECOVERY_FILE
    )

    write_audit_log(
        db=db,
        action="SECURE_RECOVERY_VIEWED",
        username=current_user.username,
        resource="/api/recovery/secure",
        method="GET",
        status_code=200,
    )

    return {
        "user": current_user.username,
        "role": current_user.role,
        "count": int(
            len(recovery)
        ),
        "items": clean_records(
            recovery,
            100,
        ),
    }


# ============================================================
# SINGLE RECOVERY CLAIM
# ============================================================

@app.get("/api/recovery/{recovery_claim_id}")
def get_recovery_claim(
    recovery_claim_id: str,
):

    dataframe = load_csv(
        RECOVERY_FILE
    )

    if dataframe.empty:
        raise HTTPException(
            status_code=404,
            detail="Recovery data not found.",
        )

    if (
        "recovery_claim_id"
        not in dataframe.columns
    ):
        raise HTTPException(
            status_code=404,
            detail="Recovery claim ID column not found.",
        )

    matches = dataframe[
        dataframe["recovery_claim_id"]
        .astype(str)
        == recovery_claim_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Recovery claim not found.",
        )

    return matches.iloc[0].to_dict()


# ============================================================
# VENDORS
# ============================================================

@app.get("/api/vendors")
def get_vendors(
    vendor_risk_tier: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        VENDOR_FILE
    )

    if dataframe.empty:
        return {
            "count": 0,
            "items": [],
        }

    if (
        vendor_risk_tier
        and "vendor_risk_tier"
        in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["vendor_risk_tier"]
            .astype(str)
            .str.upper()
            == vendor_risk_tier.upper()
        ]

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# SINGLE VENDOR
# ============================================================

@app.get("/api/vendors/{vendor_id}")
def get_vendor(
    vendor_id: str,
):

    dataframe = load_csv(
        VENDOR_FILE
    )

    if dataframe.empty:
        raise HTTPException(
            status_code=404,
            detail="Vendor analytics not found.",
        )

    if "vendor_id" not in dataframe.columns:
        raise HTTPException(
            status_code=404,
            detail="Vendor ID column not found.",
        )

    matches = dataframe[
        dataframe["vendor_id"]
        .astype(str)
        == vendor_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found.",
        )

    return matches.iloc[0].to_dict()


# ============================================================
# INVESTIGATIONS
# ============================================================

@app.get("/api/investigations")
def get_investigations(
    investigation_priority: Optional[str] = None,
    investigation_category: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        INVESTIGATIONS_FILE
    )

    if dataframe.empty:
        return {
            "count": 0,
            "items": [],
        }

    if (
        investigation_priority
        and "investigation_priority"
        in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe[
                "investigation_priority"
            ]
            .astype(str)
            .str.upper()
            == investigation_priority.upper()
        ]

    if (
        investigation_category
        and "investigation_category"
        in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe[
                "investigation_category"
            ]
            .astype(str)
            .str.upper()
            == investigation_category.upper()
        ]

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# INVESTIGATION PACKETS
# ============================================================

@app.get("/api/investigation-packets")
def get_investigation_packets(
    packet_status: Optional[str] = None,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        PACKETS_FILE
    )

    if dataframe.empty:
        return {
            "count": 0,
            "items": [],
        }

    if (
        packet_status
        and "packet_status"
        in dataframe.columns
    ):
        dataframe = dataframe[
            dataframe["packet_status"]
            .astype(str)
            .str.upper()
            == packet_status.upper()
        ]

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# ML ANOMALIES
# ============================================================

@app.get("/api/anomalies")
def get_anomalies(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        ANOMALIES_FILE
    )

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# CONTRACT COMPLIANCE
# ============================================================

@app.get("/api/contract-compliance")
def get_contract_compliance(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):

    dataframe = load_csv(
        CONTRACT_COMPLIANCE_FILE
    )

    return {
        "count": int(
            len(dataframe)
        ),
        "items": clean_records(
            dataframe,
            limit,
        ),
    }


# ============================================================
# RECOVERY ANALYTICS
# ============================================================

@app.get("/api/recovery-analytics")
def get_recovery_analytics():

    dataframe = load_csv(
        RECOVERY_ANALYTICS_FILE
    )

    cleaned = clean_records(
        dataframe,
        500,
    )

    return {
        "count": int(
            len(cleaned)
        ),
        "rows": int(
            len(dataframe)
        ),
        "columns": list(
            dataframe.columns
        ),
        "data": cleaned,
        "items": cleaned,
    }


# ============================================================
# AUTH - REGISTER
# ============================================================

@app.post(
    "/api/auth/register",
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    username: str,
    password: str,
    role: str = "VIEWER",
    db: Session = Depends(get_db),
):

    username = username.strip()
    role = role.upper().strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty.",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid role. Allowed roles: "
                + ", ".join(
                    sorted(ALLOWED_ROLES)
                )
            ),
        )

    existing_user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists.",
        )

    user = User(
        username=username,
        password_hash=hash_password(
            password
        ),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    write_audit_log(
        db=db,
        action="USER_CREATED",
        username=username,
        resource="/api/auth/register",
        method="POST",
        status_code=201,
        details={
            "role": role,
        },
    )

    return {
        "message": "User registered successfully.",
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    }


# ============================================================
# AUTH - LOGIN
# ============================================================

@app.post("/api/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.username
            == form_data.username
        )
        .first()
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.password_hash,
        )
    ):
        write_audit_log(
            db=db,
            action="LOGIN_FAILED",
            username=form_data.username,
            resource="/api/auth/login",
            method="POST",
            status_code=401,
        )

        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive.",
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role,
    )

    write_audit_log(
        db=db,
        action="LOGIN",
        username=user.username,
        resource="/api/auth/login",
        method="POST",
        status_code=200,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }


# ============================================================
# AUTH - CURRENT USER
# ============================================================

@app.get("/api/auth/me")
def get_my_profile(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    write_audit_log(
        db=db,
        action="PROFILE_VIEWED",
        username=current_user.username,
        resource="/api/auth/me",
        method="GET",
        status_code=200,
    )

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }


# ============================================================
# ADMIN - USERS
# ============================================================

@app.get("/api/admin/users")
def list_users(
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
    db: Session = Depends(get_db),
):

    users = (
        db.query(User)
        .order_by(
            User.id.asc()
        )
        .all()
    )

    write_audit_log(
        db=db,
        action="ADMIN_USER_LIST_VIEWED",
        username=current_user.username,
        resource="/api/admin/users",
        method="GET",
        status_code=200,
    )

    return {
        "count": len(users),
        "items": [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ],
    }


# ============================================================
# ADMIN - AUDIT LOGS
# ============================================================

@app.get("/api/admin/audit-logs")
def get_audit_logs(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
    db: Session = Depends(get_db),
):

    logs = (
        db.query(AuditLog)
        .order_by(
            AuditLog.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    write_audit_log(
        db=db,
        action="AUDIT_LOGS_VIEWED",
        username=current_user.username,
        resource="/api/admin/audit-logs",
        method="GET",
        status_code=200,
        details={
            "limit": limit,
        },
    )

    return {
        "count": len(logs),
        "items": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "method": log.method,
                "status_code": log.status_code,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }


# ============================================================
# APPLICATION STARTUP INFORMATION
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Ensure database tables exist when the API starts.
    """

    Base.metadata.create_all(
        bind=engine
    )