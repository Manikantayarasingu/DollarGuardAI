"""
DollarGuard AI - Contract Price Mismatch Detector

Detects cases where an invoice charges a higher unit price
than the contracted price.

Flow:
Invoice -> Purchase Order -> Contract

Output:
- Claim ID
- Vendor
- Invoice
- Contract
- SKU
- Original Amount
- Expected Amount
- Potential Leakage
- Variance %
- Confidence
- Risk Level
- Evidence
- Status
"""

from datetime import datetime

import pandas as pd
from sqlalchemy import text

from app.database.connection import engine


LEAKAGE_TYPE = "PRICE_MISMATCH"


def calculate_risk_level(leakage_amount: float) -> str:
    """
    Assign a risk level based on potential leakage amount.
    """

    if leakage_amount >= 500000:
        return "CRITICAL"

    if leakage_amount >= 100000:
        return "HIGH"

    if leakage_amount >= 25000:
        return "MEDIUM"

    return "LOW"


def detect_price_mismatches(
    minimum_leakage: float = 1.0,
) -> pd.DataFrame:
    """
    Detect invoice price mismatches against active contracts.

    Returns:
        pandas.DataFrame containing detected leakage claims.
    """

    query = text(
        """
        SELECT
            i.invoice_id,
            i.po_id,
            i.vendor_id,
            i.sku,
            i.quantity,
            i.unit_price AS invoice_unit_price,
            i.invoice_amount,
            i.invoice_date,
            i.currency,
            i.status AS invoice_status,

            po.contract_id,
            po.unit_price AS po_unit_price,
            po.po_amount,
            po.po_date,

            c.contract_price,
            c.product_name,
            c.rebate_percentage,
            c.valid_from,
            c.valid_to,
            c.payment_terms,
            c.status AS contract_status

        FROM invoices i

        INNER JOIN purchase_orders po
            ON i.po_id = po.po_id

        INNER JOIN contracts c
            ON po.contract_id = c.contract_id

        WHERE
            c.status = 'ACTIVE'
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql_query(query, connection)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "claim_id",
                "vendor_id",
                "invoice_id",
                "po_id",
                "contract_id",
                "sku",
                "product_name",
                "leakage_type",
                "quantity",
                "contract_unit_price",
                "invoice_unit_price",
                "original_amount",
                "expected_amount",
                "potential_leakage",
                "variance_percentage",
                "confidence_score",
                "risk_level",
                "currency",
                "evidence",
                "status",
                "detected_at",
            ]
        )

    # ---------------------------------------------------------
    # Convert numeric fields safely
    # ---------------------------------------------------------

    numeric_columns = [
        "quantity",
        "invoice_unit_price",
        "invoice_amount",
        "contract_price",
        "po_unit_price",
        "po_amount",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Remove records where essential pricing information is missing
    df = df.dropna(
        subset=[
            "quantity",
            "invoice_unit_price",
            "contract_price",
        ]
    ).copy()

    if df.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Calculate expected and actual amounts
    # ---------------------------------------------------------

    df["expected_amount"] = (
        df["quantity"] * df["contract_price"]
    )

    # Prefer the actual invoice amount.
    # If unavailable, calculate from quantity × invoice price.
    df["original_amount"] = df["invoice_amount"]

    df["original_amount"] = df["original_amount"].fillna(
        df["quantity"] * df["invoice_unit_price"]
    )

    # ---------------------------------------------------------
    # Calculate potential leakage
    # ---------------------------------------------------------

    df["potential_leakage"] = (
        df["original_amount"] - df["expected_amount"]
    )

    # Only retain cases where invoice price is greater
    # than the contracted price.
    df = df[
        (df["invoice_unit_price"] > df["contract_price"])
        & (df["potential_leakage"] >= minimum_leakage)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Calculate price variance
    # ---------------------------------------------------------

    df["variance_percentage"] = (
        (
            df["invoice_unit_price"]
            - df["contract_price"]
        )
        / df["contract_price"]
    ) * 100

    df["variance_percentage"] = (
        df["variance_percentage"]
        .replace([float("inf"), -float("inf")], 0)
        .round(2)
    )

    # ---------------------------------------------------------
    # Confidence score
    # ---------------------------------------------------------

    # Exact relationship:
    # Invoice -> PO -> Contract
    #
    # Because the detector uses the contract linked directly
    # to the purchase order, confidence is high.

    df["confidence_score"] = 98.0

    # ---------------------------------------------------------
    # Risk level
    # ---------------------------------------------------------

    df["risk_level"] = df["potential_leakage"].apply(
        calculate_risk_level
    )

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    def create_evidence(row):
        return (
            f"Invoice {row['invoice_id']} charged "
            f"{row['invoice_unit_price']:.2f} per unit for SKU "
            f"{row['sku']}, while the linked contract "
            f"{row['contract_id']} specifies "
            f"{row['contract_price']:.2f} per unit. "
            f"Quantity: {row['quantity']:.0f}. "
            f"Expected amount: {row['expected_amount']:.2f}. "
            f"Actual invoice amount: {row['original_amount']:.2f}. "
            f"Potential leakage: "
            f"{row['potential_leakage']:.2f} "
            f"({row['variance_percentage']:.2f}% price variance)."
        )

    df["evidence"] = df.apply(
        create_evidence,
        axis=1,
    )

    # ---------------------------------------------------------
    # Claim IDs
    # ---------------------------------------------------------

    df["claim_id"] = (
        "CLM-PRICE-"
        + df["invoice_id"].astype(str)
    )

    # ---------------------------------------------------------
    # Static metadata
    # ---------------------------------------------------------

    df["leakage_type"] = LEAKAGE_TYPE

    df["status"] = "NEW"

    detected_at = datetime.utcnow().isoformat()

    df["detected_at"] = detected_at

    # ---------------------------------------------------------
    # Final output structure
    # ---------------------------------------------------------

    result = df[
        [
            "claim_id",
            "vendor_id",
            "invoice_id",
            "po_id",
            "contract_id",
            "sku",
            "product_name",
            "leakage_type",
            "quantity",
            "contract_price",
            "invoice_unit_price",
            "original_amount",
            "expected_amount",
            "potential_leakage",
            "variance_percentage",
            "confidence_score",
            "risk_level",
            "currency",
            "evidence",
            "status",
            "detected_at",
        ]
    ].copy()

    # Rename contract price for clearer downstream usage.
    result = result.rename(
        columns={
            "contract_price": "contract_unit_price"
        }
    )

    # Sort by highest leakage first.
    result = result.sort_values(
        by="potential_leakage",
        ascending=False,
    ).reset_index(drop=True)

    return result


def print_detection_summary(
    claims: pd.DataFrame,
) -> None:
    """
    Print a human-readable summary of detected claims.
    """

    print("\n" + "=" * 70)
    print("DOLLARGUARD AI - PRICE MISMATCH DETECTION")
    print("=" * 70)

    if claims.empty:
        print("\nNo price mismatch claims detected.")
        print("=" * 70)
        return

    total_leakage = claims["potential_leakage"].sum()

    print(f"\nClaims detected       : {len(claims):,}")
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
            f"  {risk_level:<10}: {count:,}"
        )

    print("\nTop 10 Claims:")

    display_columns = [
        "claim_id",
        "vendor_id",
        "invoice_id",
        "sku",
        "contract_unit_price",
        "invoice_unit_price",
        "potential_leakage",
        "variance_percentage",
        "risk_level",
    ]

    print(
        claims[display_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":

    claims = detect_price_mismatches()

    print_detection_summary(claims)