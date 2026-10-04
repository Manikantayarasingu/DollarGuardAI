"""
DollarGuard AI - Quantity Mismatch Detector

Detects invoices where invoiced quantity exceeds the quantity
actually received.

Detection flow:

    Purchase Order
          ↓
    Goods Receipt
          ↓
       Invoice

The detector dynamically inspects the goods_receipts table so
it does not depend on an assumed column name.
"""

from datetime import datetime

import pandas as pd
from sqlalchemy import inspect, text

from app.database.connection import engine


LEAKAGE_TYPE = "QUANTITY_MISMATCH"


def get_table_columns(table_name: str) -> list[str]:
    """
    Return the actual columns available in a database table.
    """

    inspector = inspect(engine)

    return [
        column["name"]
        for column in inspector.get_columns(table_name)
    ]


def find_quantity_column(columns: list[str]) -> str | None:
    """
    Find the quantity column used by the goods_receipts table.

    Supports common naming conventions.
    """

    candidates = [
        "quantity",
        "received_quantity",
        "receipt_quantity",
        "goods_received_quantity",
        "qty",
        "received_qty",
        "quantity_received",
    ]

    column_lookup = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in column_lookup:
            return column_lookup[candidate.lower()]

    return None


def find_receipt_id_column(columns: list[str]) -> str | None:
    """
    Find the receipt identifier column.
    """

    candidates = [
        "receipt_id",
        "goods_receipt_id",
        "gr_id",
        "id",
    ]

    column_lookup = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in column_lookup:
            return column_lookup[candidate.lower()]

    return None


def calculate_risk_level(
    leakage_amount: float,
) -> str:
    """Assign risk level based on potential leakage."""

    if leakage_amount >= 500000:
        return "CRITICAL"

    if leakage_amount >= 100000:
        return "HIGH"

    if leakage_amount >= 25000:
        return "MEDIUM"

    return "LOW"


def empty_result() -> pd.DataFrame:
    """Return an empty result with the expected schema."""

    return pd.DataFrame(
        columns=[
            "claim_id",
            "vendor_id",
            "invoice_id",
            "po_id",
            "contract_id",
            "sku",
            "leakage_type",
            "po_quantity",
            "received_quantity",
            "invoice_quantity",
            "excess_quantity",
            "contract_unit_price",
            "invoice_unit_price",
            "original_amount",
            "expected_amount",
            "potential_leakage",
            "variance_percentage",
            "confidence_score",
            "risk_level",
            "currency",
            "receipt_id",
            "evidence",
            "status",
            "detected_at",
        ]
    )


def detect_quantity_mismatches(
    minimum_leakage: float = 1.0,
) -> pd.DataFrame:
    """
    Detect invoices where invoiced quantity exceeds
    received quantity.
    """

    # ---------------------------------------------------------
    # Inspect actual goods_receipts schema
    # ---------------------------------------------------------

    goods_receipt_columns = get_table_columns(
        "goods_receipts"
    )

    quantity_column = find_quantity_column(
        goods_receipt_columns
    )

    receipt_id_column = find_receipt_id_column(
        goods_receipt_columns
    )

    if quantity_column is None:
        print("\nERROR: Could not find a quantity column in")
        print("the goods_receipts table.")

        print("\nAvailable goods_receipts columns:")

        for column in goods_receipt_columns:
            print(f"  - {column}")

        return empty_result()

    if receipt_id_column is None:
        print("\nERROR: Could not find a receipt ID column.")
        print("\nAvailable goods_receipts columns:")

        for column in goods_receipt_columns:
            print(f"  - {column}")

        return empty_result()

    # ---------------------------------------------------------
    # Build SQL using the ACTUAL column names
    # ---------------------------------------------------------

    query = text(
        f"""
        SELECT
            i.invoice_id,
            i.po_id,
            i.vendor_id,
            i.sku,
            i.quantity AS invoice_quantity,
            i.unit_price AS invoice_unit_price,
            i.invoice_amount,
            i.invoice_date,
            i.currency,

            po.quantity AS po_quantity,
            po.unit_price AS po_unit_price,
            po.contract_id,
            po.po_amount,

            gr."{quantity_column}" AS received_quantity,
            gr."{receipt_id_column}" AS receipt_id

        FROM invoices i

        INNER JOIN purchase_orders po
            ON i.po_id = po.po_id

        INNER JOIN goods_receipts gr
            ON i.po_id = gr.po_id
        """
    )

    # ---------------------------------------------------------
    # Execute query
    # ---------------------------------------------------------

    with engine.connect() as connection:
        df = pd.read_sql_query(
            query,
            connection,
        )

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Convert numeric fields
    # ---------------------------------------------------------

    numeric_columns = [
        "invoice_quantity",
        "invoice_unit_price",
        "invoice_amount",
        "po_quantity",
        "po_unit_price",
        "received_quantity",
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
            "invoice_id",
            "po_id",
            "invoice_quantity",
            "received_quantity",
            "po_unit_price",
        ]
    ).copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Aggregate multiple goods receipts
    # ---------------------------------------------------------

    receipt_totals = (
        df.groupby(
            ["po_id"],
            dropna=False,
        )
        .agg(
            total_received_quantity=(
                "received_quantity",
                "sum",
            ),
            receipt_ids=(
                "receipt_id",
                lambda values: ", ".join(
                    values.astype(str).unique()
                ),
            ),
        )
        .reset_index()
    )

    # Keep one invoice/PO record before merging totals.
    df = df.drop_duplicates(
        subset=[
            "invoice_id",
            "po_id",
        ]
    ).copy()

    df = df.drop(
        columns=[
            "received_quantity",
            "receipt_id",
        ],
        errors="ignore",
    )

    df = df.merge(
        receipt_totals,
        on="po_id",
        how="left",
    )

    # ---------------------------------------------------------
    # Calculate excess invoiced quantity
    # ---------------------------------------------------------

    df["excess_quantity"] = (
        df["invoice_quantity"]
        - df["total_received_quantity"]
    )

    df = df[
        df["excess_quantity"] > 0
    ].copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Contract / PO price
    # ---------------------------------------------------------

    df["contract_unit_price"] = (
        df["po_unit_price"]
    )

    # ---------------------------------------------------------
    # Expected amount
    # ---------------------------------------------------------

    df["expected_amount"] = (
        df["total_received_quantity"]
        * df["contract_unit_price"]
    )

    # ---------------------------------------------------------
    # Original invoice amount
    # ---------------------------------------------------------

    df["original_amount"] = (
        df["invoice_amount"]
    )

    df["original_amount"] = (
        df["original_amount"]
        .fillna(
            df["invoice_quantity"]
            * df["invoice_unit_price"]
        )
    )

    # ---------------------------------------------------------
    # Potential leakage
    # ---------------------------------------------------------

    df["potential_leakage"] = (
        df["excess_quantity"]
        * df["contract_unit_price"]
    )

    df = df[
        df["potential_leakage"]
        >= minimum_leakage
    ].copy()

    if df.empty:
        return empty_result()

    # ---------------------------------------------------------
    # Quantity variance percentage
    # ---------------------------------------------------------

    df["variance_percentage"] = (
        df["excess_quantity"]
        / df["total_received_quantity"]
    ) * 100

    df["variance_percentage"] = (
        df["variance_percentage"]
        .replace(
            [float("inf"), -float("inf")],
            0,
        )
        .round(2)
    )

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    df["confidence_score"] = 98.0

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
        return (
            f"Invoice {row['invoice_id']} contains "
            f"{row['invoice_quantity']:.0f} units of SKU "
            f"{row['sku']}, while goods receipts linked "
            f"to PO {row['po_id']} show only "
            f"{row['total_received_quantity']:.0f} units "
            f"received. "
            f"Excess invoiced quantity: "
            f"{row['excess_quantity']:.0f} units. "
            f"PO/contract unit price: "
            f"{row['contract_unit_price']:.2f}. "
            f"Potential leakage: "
            f"{row['potential_leakage']:.2f}."
        )

    df["evidence"] = df.apply(
        create_evidence,
        axis=1,
    )

    # ---------------------------------------------------------
    # Claim ID
    # ---------------------------------------------------------

    df["claim_id"] = (
        "CLM-QTY-"
        + df["invoice_id"].astype(str)
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
            "invoice_id",
            "po_id",
            "contract_id",
            "sku",
            "leakage_type",
            "po_quantity",
            "total_received_quantity",
            "invoice_quantity",
            "excess_quantity",
            "contract_unit_price",
            "invoice_unit_price",
            "original_amount",
            "expected_amount",
            "potential_leakage",
            "variance_percentage",
            "confidence_score",
            "risk_level",
            "currency",
            "receipt_ids",
            "evidence",
            "status",
            "detected_at",
        ]
    ].copy()

    result = result.rename(
        columns={
            "total_received_quantity": "received_quantity",
            "receipt_ids": "receipt_id",
        }
    )

    result = result.sort_values(
        by="potential_leakage",
        ascending=False,
    ).reset_index(drop=True)

    return result


def print_detection_summary(
    claims: pd.DataFrame,
) -> None:
    """Print quantity mismatch detection results."""

    print("\n" + "=" * 70)
    print("DOLLARGUARD AI - QUANTITY MISMATCH DETECTION")
    print("=" * 70)

    if claims.empty:
        print("\nNo quantity mismatch claims detected.")
        print("=" * 70)
        return

    total_leakage = (
        claims["potential_leakage"].sum()
    )

    total_excess_quantity = (
        claims["excess_quantity"].sum()
    )

    print(
        f"\nClaims detected       : "
        f"{len(claims):,}"
    )

    print(
        f"Excess quantity       : "
        f"{total_excess_quantity:,.0f} units"
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
        "sku",
        "received_quantity",
        "invoice_quantity",
        "excess_quantity",
        "potential_leakage",
        "risk_level",
    ]

    print(
        claims[display_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":

    claims = detect_quantity_mismatches()

    print_detection_summary(claims)