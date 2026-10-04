"""
DollarGuard AI - Missing Rebate Detector

Detects potential revenue leakage caused by rebates that should have
been received but are missing, incomplete, or not credited.

Detection flow:

    Contract
        ↓
    Purchase Order
        ↓
      Rebate
        ↓
    Missing Rebate Claim
"""

from datetime import datetime

import pandas as pd
from sqlalchemy import inspect, text

from app.database.connection import engine


LEAKAGE_TYPE = "MISSING_REBATE"


# ============================================================
# SCHEMA HELPERS
# ============================================================

def get_table_columns(table_name: str) -> list[str]:
    """Return the actual columns available in a database table."""

    inspector = inspect(engine)

    return [
        column["name"]
        for column in inspector.get_columns(table_name)
    ]


def find_column(
    columns: list[str],
    candidates: list[str],
) -> str | None:
    """
    Find a column using a list of possible column names.
    Matching is case-insensitive.
    """

    column_lookup = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in column_lookup:
            return column_lookup[candidate.lower()]

    return None


# ============================================================
# RISK
# ============================================================

def calculate_risk_level(
    leakage_amount: float,
) -> str:
    """Assign risk level based on potential missing rebate."""

    if leakage_amount >= 500000:
        return "CRITICAL"

    if leakage_amount >= 100000:
        return "HIGH"

    if leakage_amount >= 25000:
        return "MEDIUM"

    return "LOW"


# ============================================================
# EMPTY RESULT
# ============================================================

def empty_result() -> pd.DataFrame:
    """Return an empty result with the expected schema."""

    return pd.DataFrame(
        columns=[
            "claim_id",
            "vendor_id",
            "contract_id",
            "po_id",
            "rebate_id",
            "rebate_type",
            "rebate_percentage",
            "rebate_amount",
            "credited_amount",
            "potential_leakage",
            "currency",
            "confidence_score",
            "risk_level",
            "evidence",
            "status",
            "detected_at",
        ]
    )


# ============================================================
# DETECTOR
# ============================================================

def detect_missing_rebates(
    minimum_leakage: float = 1.0,
) -> pd.DataFrame:
    """
    Detect rebates where the expected rebate amount is greater
    than the amount actually credited.

    The function dynamically discovers the relevant columns in
    the rebates table.
    """

    # ---------------------------------------------------------
    # Inspect table schemas
    # ---------------------------------------------------------

    rebate_columns = get_table_columns("rebates")
    contract_columns = get_table_columns("contracts")
    po_columns = get_table_columns("purchase_orders")

    # ---------------------------------------------------------
    # Identify rebate columns
    # ---------------------------------------------------------

    rebate_id_column = find_column(
        rebate_columns,
        [
            "rebate_id",
            "rebate_code",
            "id",
        ],
    )

    vendor_id_column = find_column(
        rebate_columns,
        [
            "vendor_id",
            "vendor",
        ],
    )

    contract_id_column = find_column(
        rebate_columns,
        [
            "contract_id",
            "contract",
        ],
    )

    po_id_column = find_column(
        rebate_columns,
        [
            "po_id",
            "purchase_order_id",
            "purchase_order",
        ],
    )

    rebate_percentage_column = find_column(
        rebate_columns,
        [
            "rebate_percentage",
            "rebate_percent",
            "percentage",
            "rate",
            "rebate_rate",
        ],
    )

    rebate_amount_column = find_column(
        rebate_columns,
        [
            "rebate_amount",
            "expected_rebate",
            "expected_rebate_amount",
            "eligible_rebate",
            "eligible_rebate_amount",
            "amount",
        ],
    )

    credited_amount_column = find_column(
        rebate_columns,
        [
            "credited_amount",
            "credit_amount",
            "received_amount",
            "paid_amount",
            "actual_rebate",
            "actual_rebate_amount",
            "received_rebate",
        ],
    )

    currency_column = find_column(
        rebate_columns,
        [
            "currency",
            "currency_code",
        ],
    )

    rebate_type_column = find_column(
        rebate_columns,
        [
            "rebate_type",
            "type",
            "rebate_category",
            "category",
        ],
    )

    # ---------------------------------------------------------
    # Validate required rebate columns
    # ---------------------------------------------------------

    required_columns = {
        "rebate_id": rebate_id_column,
        "vendor_id": vendor_id_column,
        "rebate amount": rebate_amount_column,
        "credited amount": credited_amount_column,
    }

    missing_columns = [
        name
        for name, column in required_columns.items()
        if column is None
    ]

    if missing_columns:

        print("\nERROR: Could not identify required rebate columns.")

        print(
            "\nMissing logical columns:"
        )

        for column in missing_columns:
            print(f"  - {column}")

        print(
            "\nAvailable rebates columns:"
        )

        for column in rebate_columns:
            print(f"  - {column}")

        return empty_result()

    # ---------------------------------------------------------
    # Build optional SQL expressions
    # ---------------------------------------------------------

    contract_select = "NULL AS contract_id"

    if contract_id_column:
        contract_select = (
            f'r."{contract_id_column}" AS contract_id'
        )

    po_select = "NULL AS po_id"

    if po_id_column:
        po_select = (
            f'r."{po_id_column}" AS po_id'
        )

    percentage_select = "NULL AS rebate_percentage"

    if rebate_percentage_column:
        percentage_select = (
            f'r."{rebate_percentage_column}" '
            f'AS rebate_percentage'
        )

    currency_select = "'INR' AS currency"

    if currency_column:
        currency_select = (
            f'r."{currency_column}" AS currency'
        )

    rebate_type_select = "'REBATE' AS rebate_type"

    if rebate_type_column:
        rebate_type_select = (
            f'r."{rebate_type_column}" AS rebate_type'
        )

    # ---------------------------------------------------------
    # Build query
    # ---------------------------------------------------------

    query = text(
        f"""
        SELECT

            r."{rebate_id_column}" AS rebate_id,

            r."{vendor_id_column}" AS vendor_id,

            {contract_select},

            {po_select},

            {rebate_type_select},

            {percentage_select},

            r."{rebate_amount_column}"
                AS rebate_amount,

            r."{credited_amount_column}"
                AS credited_amount,

            {currency_select}

        FROM rebates r
        """
    )

    # ---------------------------------------------------------
    # Execute query
    # ---------------------------------------------------------

    try:

        with engine.connect() as connection:

            df = pd.read_sql_query(
                query,
                connection,
            )

    except Exception as error:

        print("\nERROR while reading rebates table:")
        print(error)

        print("\nAvailable rebates columns:")

        for column in rebate_columns:
            print(f"  - {column}")

        return empty_result()

    # ---------------------------------------------------------
    # Empty database
    # ---------------------------------------------------------

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Convert numeric fields
    # ---------------------------------------------------------

    numeric_columns = [
        "rebate_percentage",
        "rebate_amount",
        "credited_amount",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # Remove invalid records
    # ---------------------------------------------------------

    df = df.dropna(
        subset=[
            "rebate_id",
            "vendor_id",
            "rebate_amount",
            "credited_amount",
        ]
    ).copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Calculate missing rebate
    # ---------------------------------------------------------

    df["potential_leakage"] = (
        df["rebate_amount"]
        - df["credited_amount"]
    )

    # Only positive missing rebates are leakage.
    df = df[
        df["potential_leakage"] > 0
    ].copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Minimum leakage filter
    # ---------------------------------------------------------

    df = df[
        df["potential_leakage"]
        >= minimum_leakage
    ].copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    df["confidence_score"] = 97.0

    # ---------------------------------------------------------
    # Risk
    # ---------------------------------------------------------

    df["risk_level"] = (
        df["potential_leakage"]
        .apply(calculate_risk_level)
    )

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    def create_evidence(row):

        rebate_percentage = row[
            "rebate_percentage"
        ]

        if pd.isna(rebate_percentage):

            percentage_text = (
                "rebate percentage not specified"
            )

        else:

            percentage_text = (
                f"rebate rate "
                f"{rebate_percentage:.2f}%"
            )

        return (
            f"Rebate {row['rebate_id']} for vendor "
            f"{row['vendor_id']} shows an expected rebate "
            f"of {row['rebate_amount']:.2f}, but only "
            f"{row['credited_amount']:.2f} was credited. "
            f"Missing rebate amount: "
            f"{row['potential_leakage']:.2f}. "
            f"{percentage_text}."
        )

    df["evidence"] = df.apply(
        create_evidence,
        axis=1,
    )

    # ---------------------------------------------------------
    # Claim ID
    # ---------------------------------------------------------

    df["claim_id"] = (
        "CLM-REBATE-"
        + df["rebate_id"].astype(str)
    )

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    df["leakage_type"] = LEAKAGE_TYPE

    df["status"] = "NEW"

    df["detected_at"] = (
        datetime.utcnow().isoformat()
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    result = df[
        [
            "claim_id",
            "vendor_id",
            "contract_id",
            "po_id",
            "rebate_id",
            "rebate_type",
            "rebate_percentage",
            "rebate_amount",
            "credited_amount",
            "potential_leakage",
            "currency",
            "confidence_score",
            "risk_level",
            "evidence",
            "status",
            "detected_at",
        ]
    ].copy()

    result = result.sort_values(
        by="potential_leakage",
        ascending=False,
    ).reset_index(drop=True)

    return result


# ============================================================
# SUMMARY
# ============================================================

def print_detection_summary(
    claims: pd.DataFrame,
) -> None:
    """Print missing rebate detection results."""

    print("\n" + "=" * 70)
    print(
        "DOLLARGUARD AI - MISSING REBATE DETECTION"
    )
    print("=" * 70)

    if claims.empty:

        print(
            "\nNo missing rebate claims detected."
        )

        print("=" * 70)

        return

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    total_leakage = (
        claims["potential_leakage"].sum()
    )

    total_expected = (
        claims["rebate_amount"].sum()
    )

    total_credited = (
        claims["credited_amount"].sum()
    )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    print(
        f"\nClaims detected       : "
        f"{len(claims):,}"
    )

    print(
        f"Expected rebates     : "
        f"₹{total_expected:,.2f}"
    )

    print(
        f"Credited rebates     : "
        f"₹{total_credited:,.2f}"
    )

    print(
        f"Potential leakage     : "
        f"₹{total_leakage:,.2f}"
    )

    # ---------------------------------------------------------
    # Risk distribution
    # ---------------------------------------------------------

    print("\nRisk Distribution:")

    risk_counts = (
        claims["risk_level"]
        .value_counts()
        .sort_index()
    )

    for risk_level, count in risk_counts.items():

        print(
            f"  {risk_level:<10}: "
            f"{count:,}"
        )

    # ---------------------------------------------------------
    # Top claims
    # ---------------------------------------------------------

    print("\nTop 10 Claims:")

    display_columns = [
        "claim_id",
        "vendor_id",
        "rebate_id",
        "rebate_amount",
        "credited_amount",
        "potential_leakage",
        "risk_level",
    ]

    print(
        claims[
            display_columns
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    claims = detect_missing_rebates()

    print_detection_summary(
        claims
    )