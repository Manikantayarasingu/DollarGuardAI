"""
DollarGuard AI - Duplicate Payment Detector

Detects invoices that appear to have been paid multiple times.

Detection logic:
    Payments -> Invoice

A duplicate payment is identified when:
    - The same invoice has multiple payment records
    - Total payments exceed the invoice amount

The detector intentionally uses only the columns required
for duplicate-payment analysis so it remains compatible
with the synthetic payment schema.
"""

from datetime import datetime

import pandas as pd
from sqlalchemy import text

from app.database.connection import engine


LEAKAGE_TYPE = "DUPLICATE_PAYMENT"


def calculate_risk_level(leakage_amount: float) -> str:
    """Assign risk level based on potential duplicate payment."""

    if leakage_amount >= 500000:
        return "CRITICAL"

    if leakage_amount >= 100000:
        return "HIGH"

    if leakage_amount >= 25000:
        return "MEDIUM"

    return "LOW"


def detect_duplicate_payments(
    minimum_leakage: float = 1.0,
) -> pd.DataFrame:
    """
    Detect invoices that have been paid more than once.

    Returns:
        DataFrame containing duplicate-payment claims.
    """

    # ---------------------------------------------------------
    # Read only columns that actually exist and are required.
    # ---------------------------------------------------------

    query = text(
        """
        SELECT
            p.payment_id,
            p.invoice_id,
            p.vendor_id,
            p.payment_date,
            p.payment_amount,

            i.invoice_amount,
            i.po_id,
            i.sku,
            i.invoice_date,
            i.currency

        FROM payments p

        INNER JOIN invoices i
            ON p.invoice_id = i.invoice_id
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql_query(
            query,
            connection,
        )

    # ---------------------------------------------------------
    # Empty database result
    # ---------------------------------------------------------

    if df.empty:
        return pd.DataFrame(
            columns=[
                "claim_id",
                "vendor_id",
                "invoice_id",
                "po_id",
                "sku",
                "leakage_type",
                "invoice_amount",
                "total_paid_amount",
                "duplicate_payment_amount",
                "payment_count",
                "payment_ids",
                "confidence_score",
                "risk_level",
                "currency",
                "evidence",
                "status",
                "detected_at",
            ]
        )

    # ---------------------------------------------------------
    # Convert numeric columns
    # ---------------------------------------------------------

    df["payment_amount"] = pd.to_numeric(
        df["payment_amount"],
        errors="coerce",
    )

    df["invoice_amount"] = pd.to_numeric(
        df["invoice_amount"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "payment_amount",
            "invoice_amount",
            "invoice_id",
        ]
    ).copy()

    if df.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Group all payments belonging to the same invoice
    # ---------------------------------------------------------

    grouped = (
        df.groupby(
            [
                "invoice_id",
                "vendor_id",
                "po_id",
                "sku",
                "invoice_amount",
                "currency",
            ],
            dropna=False,
        )
        .agg(
            total_paid_amount=(
                "payment_amount",
                "sum",
            ),
            payment_count=(
                "payment_id",
                "count",
            ),
            payment_ids=(
                "payment_id",
                lambda values: ", ".join(
                    values.astype(str)
                ),
            ),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # A duplicate requires at least two payments
    # ---------------------------------------------------------

    grouped = grouped[
        grouped["payment_count"] > 1
    ].copy()

    if grouped.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Calculate excess amount paid
    # ---------------------------------------------------------

    grouped["duplicate_payment_amount"] = (
        grouped["total_paid_amount"]
        - grouped["invoice_amount"]
    )

    # Only keep cases where the company actually paid
    # more than the invoice value.
    grouped = grouped[
        grouped["duplicate_payment_amount"]
        >= minimum_leakage
    ].copy()

    if grouped.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Confidence score
    # ---------------------------------------------------------

    grouped["confidence_score"] = 97.0

    grouped.loc[
        grouped["payment_count"] >= 3,
        "confidence_score",
    ] = 99.0

    # ---------------------------------------------------------
    # Risk level
    # ---------------------------------------------------------

    grouped["risk_level"] = (
        grouped["duplicate_payment_amount"]
        .apply(calculate_risk_level)
    )

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    def create_evidence(row):
        return (
            f"Invoice {row['invoice_id']} has "
            f"{int(row['payment_count'])} payment records. "
            f"Payment IDs: "
            f"[{row['payment_ids']}]. "
            f"Invoice amount: "
            f"{row['invoice_amount']:.2f}. "
            f"Total paid: "
            f"{row['total_paid_amount']:.2f}. "
            f"Potential duplicate payment: "
            f"{row['duplicate_payment_amount']:.2f}."
        )

    grouped["evidence"] = grouped.apply(
        create_evidence,
        axis=1,
    )

    # ---------------------------------------------------------
    # Generate claim ID
    # ---------------------------------------------------------

    grouped["claim_id"] = (
        "CLM-DUPPAY-"
        + grouped["invoice_id"].astype(str)
    )

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    grouped["leakage_type"] = LEAKAGE_TYPE

    grouped["status"] = "NEW"

    grouped["detected_at"] = (
        datetime.utcnow().isoformat()
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    result = grouped[
        [
            "claim_id",
            "vendor_id",
            "invoice_id",
            "po_id",
            "sku",
            "leakage_type",
            "invoice_amount",
            "total_paid_amount",
            "duplicate_payment_amount",
            "payment_count",
            "payment_ids",
            "confidence_score",
            "risk_level",
            "currency",
            "evidence",
            "status",
            "detected_at",
        ]
    ].copy()

    # ---------------------------------------------------------
    # Highest leakage first
    # ---------------------------------------------------------

    result = result.sort_values(
        by="duplicate_payment_amount",
        ascending=False,
    ).reset_index(drop=True)

    return result


def print_detection_summary(
    claims: pd.DataFrame,
) -> None:
    """Print duplicate-payment detection results."""

    print("\n" + "=" * 70)
    print("DOLLARGUARD AI - DUPLICATE PAYMENT DETECTION")
    print("=" * 70)

    if claims.empty:
        print("\nNo duplicate payment claims detected.")
        print("=" * 70)
        return

    total_leakage = (
        claims["duplicate_payment_amount"].sum()
    )

    print(
        f"\nClaims detected       : "
        f"{len(claims):,}"
    )

    print(
        f"Potential leakage     : "
        f"₹{total_leakage:,.2f}"
    )

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

    print("\nTop 10 Claims:")

    display_columns = [
        "claim_id",
        "vendor_id",
        "invoice_id",
        "invoice_amount",
        "total_paid_amount",
        "duplicate_payment_amount",
        "payment_count",
        "risk_level",
    ]

    print(
        claims[display_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":

    claims = detect_duplicate_payments()

    print_detection_summary(claims)