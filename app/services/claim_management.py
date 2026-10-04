
"""
DollarGuard AI
Claim Management & Recovery Service

Purpose:
    Convert detected leakage investigations into recovery claims.

Workflow:

    NEW
      ↓
    UNDER_REVIEW
      ↓
    CLAIM_RAISED
      ↓
    RECOVERY_IN_PROGRESS
      ↓
    RECOVERED

Alternative outcomes:

    REJECTED
    CLOSED

Output:
    data/processed/recovery_claims.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

INVESTIGATION_FILE = (
    PROCESSED_DIR / "investigation_reports.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR / "recovery_claims.csv"
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except (ValueError, TypeError):
        return default


def safe_text(value, default: str = "") -> str:

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass

    return str(value).strip()


def normalize_columns(
    dataframe: pd.DataFrame
) -> pd.DataFrame:

    dataframe = dataframe.copy()

    dataframe.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in dataframe.columns
    ]

    return dataframe


# ============================================================
# CLAIM ID
# ============================================================

def generate_recovery_claim_id(
    investigation_id: str
) -> str:

    clean_id = safe_text(
        investigation_id,
        "UNKNOWN"
    )

    if clean_id.startswith("INV-"):

        clean_id = clean_id[4:]

    return f"RC-{clean_id}"


# ============================================================
# RECOVERY CATEGORY
# ============================================================

def determine_recovery_category(
    investigation_category: str
) -> str:

    category = safe_text(
        investigation_category
    ).upper()

    mapping = {

        "PRICING":
            "SUPPLIER_PRICE_RECOVERY",

        "DUPLICATE_TRANSACTION":
            "DUPLICATE_PAYMENT_RECOVERY",

        "QUANTITY":
            "EXCESS_BILLING_RECOVERY",

        "REBATE":
            "REBATE_RECOVERY",

        "CONTRACT_COMPLIANCE":
            "CONTRACT_COMPLIANCE_RECOVERY",

        "PAYMENT_COMPLIANCE":
            "PAYMENT_COMPLIANCE_REVIEW",

    }

    return mapping.get(
        category,
        "FINANCIAL_RECOVERY"
    )


# ============================================================
# RECOVERY METHOD
# ============================================================

def determine_recovery_method(
    investigation_category: str
) -> str:

    category = safe_text(
        investigation_category
    ).upper()

    methods = {

        "PRICING":
            "Supplier credit note or invoice adjustment",

        "DUPLICATE_TRANSACTION":
            "Payment reversal or supplier refund",

        "QUANTITY":
            "Supplier credit note or invoice correction",

        "REBATE":
            "Supplier rebate credit",

        "CONTRACT_COMPLIANCE":
            "Contractual recovery claim",

        "PAYMENT_COMPLIANCE":
            "Financial review and adjustment",

    }

    return methods.get(
        category,
        "Financial recovery review"
    )


# ============================================================
# RECOVERY PRIORITY
# ============================================================

def determine_recovery_priority(
    investigation_priority: str,
    potential_leakage: float
) -> str:

    priority = safe_text(
        investigation_priority
    ).upper()

    if priority == "P1":
        return "URGENT"

    if potential_leakage >= 5_000_000:
        return "URGENT"

    if priority == "P2":
        return "HIGH"

    if potential_leakage >= 1_000_000:
        return "HIGH"

    if priority == "P3":
        return "MEDIUM"

    return "NORMAL"


# ============================================================
# CREATE CLAIM
# ============================================================

def create_recovery_claim(
    investigation: pd.Series
) -> dict:

    investigation_id = safe_text(
        investigation.get(
            "investigation_id"
        )
    )

    claim_id = safe_text(
        investigation.get(
            "claim_id"
        )
    )

    investigation_category = safe_text(
        investigation.get(
            "investigation_category"
        ),
        "OTHER"
    )

    potential_leakage = safe_float(
        investigation.get(
            "potential_leakage"
        )
    )

    confidence_score = safe_float(
        investigation.get(
            "confidence_score"
        )
    )

    investigation_priority = safe_text(
        investigation.get(
            "investigation_priority"
        ),
        "P4"
    )

    recovery_claim_id = (
        generate_recovery_claim_id(
            investigation_id
        )
    )

    recovery_category = (
        determine_recovery_category(
            investigation_category
        )
    )

    recovery_method = (
        determine_recovery_method(
            investigation_category
        )
    )

    recovery_priority = (
        determine_recovery_priority(
            investigation_priority,
            potential_leakage
        )
    )

    return {

        "recovery_claim_id":
            recovery_claim_id,

        "investigation_id":
            investigation_id,

        "original_claim_id":
            claim_id,

        "vendor_id":
            safe_text(
                investigation.get(
                    "vendor_id"
                )
            ),

        "invoice_id":
            safe_text(
                investigation.get(
                    "invoice_id"
                )
            ),

        "investigation_category":
            investigation_category,

        "recovery_category":
            recovery_category,

        "potential_leakage":
            potential_leakage,

        "claimed_amount":
            potential_leakage,

        "recovered_amount":
            0.0,

        "outstanding_amount":
            potential_leakage,

        "confidence_score":
            confidence_score,

        "risk_level":
            safe_text(
                investigation.get(
                    "risk_level"
                ),
                "LOW"
            ),

        "investigation_priority":
            investigation_priority,

        "recovery_priority":
            recovery_priority,

        "recovery_method":
            recovery_method,

        "claim_status":
            "NEW",

        "supplier_response":
            "PENDING",

        "recovery_notes":
            "",

        "created_at":
            datetime.utcnow().isoformat(),

        "updated_at":
            datetime.utcnow().isoformat(),

    }


# ============================================================
# LOAD INVESTIGATIONS
# ============================================================

def load_investigations() -> pd.DataFrame:

    if not INVESTIGATION_FILE.exists():

        print(
            "Investigation report file not found:"
        )

        print(
            f"  {INVESTIGATION_FILE}"
        )

        print()

        print(
            "Run the AI Investigator first:"
        )

        print(
            "python -m app.services.ai_investigator"
        )

        return pd.DataFrame()

    dataframe = pd.read_csv(
        INVESTIGATION_FILE
    )

    return normalize_columns(
        dataframe
    )


# ============================================================
# GENERATE RECOVERY CLAIMS
# ============================================================

def generate_recovery_claims(
    investigations: pd.DataFrame
) -> pd.DataFrame:

    if investigations.empty:

        return pd.DataFrame()

    claims = []

    print(
        f"Creating recovery claims for "
        f"{len(investigations):,} investigations..."
    )

    for _, investigation in investigations.iterrows():

        claim = create_recovery_claim(
            investigation
        )

        claims.append(claim)

    return pd.DataFrame(claims)


# ============================================================
# PRESERVE EXISTING CLAIM STATUS
# ============================================================

def preserve_existing_status(
    new_claims: pd.DataFrame
) -> pd.DataFrame:

    if not OUTPUT_FILE.exists():

        return new_claims

    try:

        existing = pd.read_csv(
            OUTPUT_FILE
        )

        existing = normalize_columns(
            existing
        )

    except Exception:

        return new_claims

    if existing.empty:

        return new_claims

    existing_columns = [
        "recovery_claim_id",
        "claim_status",
        "supplier_response",
        "recovered_amount",
        "recovery_notes",
        "created_at",
        "updated_at",
    ]

    existing_columns = [
        column
        for column in existing_columns
        if column in existing.columns
    ]

    if "recovery_claim_id" not in existing_columns:

        return new_claims

    existing_status = existing[
        existing_columns
    ].copy()

    merged = new_claims.merge(
        existing_status,
        on="recovery_claim_id",
        how="left",
        suffixes=(
            "",
            "_existing"
        )
    )

    for column in [
        "claim_status",
        "supplier_response",
        "recovered_amount",
        "recovery_notes",
        "created_at",
    ]:

        existing_column = (
            f"{column}_existing"
        )

        if existing_column in merged.columns:

            mask = (
                merged[existing_column]
                .notna()
            )

            merged.loc[
                mask,
                column
            ] = merged.loc[
                mask,
                existing_column
            ]

            merged.drop(
                columns=[
                    existing_column
                ],
                inplace=True
            )

    merged["updated_at"] = (
        datetime.utcnow().isoformat()
    )

    merged["recovered_amount"] = (
        pd.to_numeric(
            merged["recovered_amount"],
            errors="coerce"
        )
        .fillna(0)
    )

    merged["claimed_amount"] = (
        pd.to_numeric(
            merged["claimed_amount"],
            errors="coerce"
        )
        .fillna(0)
    )

    merged["outstanding_amount"] = (
        merged["claimed_amount"]
        - merged["recovered_amount"]
    ).clip(lower=0)

    return merged


# ============================================================
# SAVE
# ============================================================

def save_recovery_claims(
    dataframe: pd.DataFrame
) -> None:

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    dataframe: pd.DataFrame
) -> None:

    print()

    print("=" * 70)

    print(
        "DOLLARGUARD AI - RECOVERY CLAIM MANAGEMENT"
    )

    print("=" * 70)

    print()

    if dataframe.empty:

        print(
            "No recovery claims generated."
        )

        return

    claimed = (
        pd.to_numeric(
            dataframe["claimed_amount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    recovered = (
        pd.to_numeric(
            dataframe["recovered_amount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    outstanding = (
        pd.to_numeric(
            dataframe["outstanding_amount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    recovery_rate = (
        recovered / claimed * 100
        if claimed > 0
        else 0
    )

    print(
        f"Recovery claims       : {len(dataframe):,}"
    )

    print(
        f"Claimed amount        : ₹{claimed:,.2f}"
    )

    print(
        f"Recovered amount      : ₹{recovered:,.2f}"
    )

    print(
        f"Outstanding amount    : ₹{outstanding:,.2f}"
    )

    print(
        f"Recovery rate         : {recovery_rate:.2f}%"
    )

    print()

    print("Claim Status:")

    statuses = (
        dataframe["claim_status"]
        .value_counts()
    )

    for status, count in statuses.items():

        print(
            f"  {status:<25}: {count:,}"
        )

    print()

    print("Recovery Priority:")

    priorities = (
        dataframe["recovery_priority"]
        .value_counts()
    )

    for priority in [
        "URGENT",
        "HIGH",
        "MEDIUM",
        "NORMAL",
    ]:

        print(
            f"  {priority:<10}: "
            f"{priorities.get(priority, 0):,}"
        )

    print()

    print(
        "Output file:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def run_claim_management():

    print()

    print("=" * 70)

    print(
        "DOLLARGUARD AI - CLAIM MANAGEMENT"
    )

    print("=" * 70)

    print()

    investigations = (
        load_investigations()
    )

    if investigations.empty:

        return pd.DataFrame()

    new_claims = (
        generate_recovery_claims(
            investigations
        )
    )

    if new_claims.empty:

        print(
            "No claims generated."
        )

        return pd.DataFrame()

    final_claims = (
        preserve_existing_status(
            new_claims
        )
    )

    save_recovery_claims(
        final_claims
    )

    print_summary(
        final_claims
    )

    return final_claims


if __name__ == "__main__":

    run_claim_management()
