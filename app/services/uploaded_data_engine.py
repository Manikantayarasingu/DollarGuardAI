from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd


# ============================================================
# DOLLARGUARD AI
# UPLOADED DATA LEAKAGE ENGINE
#
# This engine analyzes user-uploaded datasets independently
# from the existing synthetic/demo pipeline.
# ============================================================


ENGINE_VERSION = "uploaded-v1.0"


# ============================================================
# HELPERS
# ============================================================

def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV safely."""
    return pd.read_csv(path)


def _find_dataset(workspace: Path, dataset_type: str) -> Optional[Path]:
    """
    Find a normalized dataset saved by upload_manager.py.
    """
    candidates = list(workspace.glob("*.csv"))

    for path in candidates:
        name = path.stem.lower()

        if dataset_type.lower() in name:
            return path

    return None


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize dataframe column names.
    """
    df = df.copy()

    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    return df


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Convert a dataframe column to numeric safely.
    """
    if column not in df.columns:
        return pd.Series(np.nan, index=df.index)

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def _text(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Convert a dataframe column to string safely.
    """
    if column not in df.columns:
        return pd.Series("", index=df.index)

    return df[column].fillna("").astype(str).str.strip()


def _risk_level(amount: float) -> str:
    """
    Risk classification based on potential leakage.

    These thresholds are analytical/demo thresholds and
    are not external financial or fraud standards.
    """
    amount = float(amount or 0)

    if amount >= 1_000_000:
        return "CRITICAL"

    if amount >= 250_000:
        return "HIGH"

    if amount >= 50_000:
        return "MEDIUM"

    return "LOW"


def _base_claim(
    claim_id: str,
    leakage_type: str,
    vendor_id: str = "",
    invoice_id: str = "",
    po_id: str = "",
    contract_id: str = "",
    rebate_id: str = "",
    sku: str = "",
    original_amount: float = 0.0,
    expected_amount: float = 0.0,
    potential_leakage: float = 0.0,
    confidence_score: float = 90.0,
    evidence: str = "",
) -> dict:

    return {
        "claim_id": claim_id,
        "leakage_type": leakage_type,
        "vendor_id": vendor_id,
        "invoice_id": invoice_id,
        "po_id": po_id,
        "contract_id": contract_id,
        "rebate_id": rebate_id,
        "sku": sku,
        "original_amount": float(original_amount or 0),
        "expected_amount": float(expected_amount or 0),
        "potential_leakage": float(potential_leakage or 0),
        "confidence_score": float(confidence_score or 0),
        "risk_level": _risk_level(potential_leakage),
        "currency": "INR",
        "evidence": evidence,
        "status": "NEW",
        "detected_at": datetime.utcnow().isoformat(),
        "engine_version": ENGINE_VERSION,
    }


# ============================================================
# PRICE MISMATCH
# ============================================================

def detect_price_mismatches(
    invoices: pd.DataFrame,
    purchase_orders: Optional[pd.DataFrame] = None,
    contracts: Optional[pd.DataFrame] = None,
) -> list[dict]:

    invoices = _clean_columns(invoices)

    results = []

    # --------------------------------------------------------
    # PO comparison
    # --------------------------------------------------------

    if purchase_orders is not None and not purchase_orders.empty:

        po = _clean_columns(purchase_orders)

        required_invoice = {
            "invoice_id",
            "vendor_id",
            "po_id",
            "sku",
            "unit_price",
            "quantity",
        }

        required_po = {
            "po_id",
            "vendor_id",
            "sku",
            "unit_price",
        }

        if required_invoice.issubset(invoices.columns) and required_po.issubset(po.columns):

            merged = invoices.merge(
                po[
                    [
                        "po_id",
                        "vendor_id",
                        "sku",
                        "unit_price",
                    ]
                ].rename(
                    columns={
                        "unit_price": "po_unit_price",
                    }
                ),
                on=["po_id", "vendor_id", "sku"],
                how="left",
            )

            merged["invoice_unit_price"] = _numeric(
                merged,
                "unit_price",
            )

            merged["po_unit_price"] = _numeric(
                merged,
                "po_unit_price",
            )

            merged["quantity_num"] = _numeric(
                merged,
                "quantity",
            )

            merged["price_difference"] = (
                merged["invoice_unit_price"]
                - merged["po_unit_price"]
            )

            merged["leakage"] = (
                merged["price_difference"]
                * merged["quantity_num"]
            )

            violations = merged[
                (merged["po_unit_price"].notna())
                & (merged["price_difference"] > 0)
                & (merged["leakage"] > 0)
            ]

            for _, row in violations.iterrows():

                leakage = float(row["leakage"])

                results.append(
                    _base_claim(
                        claim_id=f"CLM-UPLOAD-PRICE-{row['invoice_id']}",
                        leakage_type="PRICE_MISMATCH",
                        vendor_id=str(row["vendor_id"]),
                        invoice_id=str(row["invoice_id"]),
                        po_id=str(row["po_id"]),
                        sku=str(row["sku"]),
                        original_amount=float(
                            row["invoice_unit_price"]
                            * row["quantity_num"]
                        ),
                        expected_amount=float(
                            row["po_unit_price"]
                            * row["quantity_num"]
                        ),
                        potential_leakage=leakage,
                        confidence_score=97.0,
                        evidence=(
                            f"Invoice unit price ₹{row['invoice_unit_price']:,.2f} "
                            f"is above PO unit price ₹{row['po_unit_price']:,.2f}; "
                            f"quantity={row['quantity_num']:,.0f}."
                        ),
                    )
                )

    # --------------------------------------------------------
    # Contract comparison
    # --------------------------------------------------------

    if contracts is not None and not contracts.empty:

        contract = _clean_columns(contracts)

        required_contract = {
            "vendor_id",
            "unit_price",
        }

        required_invoice = {
            "invoice_id",
            "vendor_id",
            "sku",
            "unit_price",
            "quantity",
        }

        if (
            required_contract.issubset(contract.columns)
            and required_invoice.issubset(invoices.columns)
        ):

            merged = invoices.merge(
                contract[
                    [
                        "vendor_id",
                        "unit_price",
                    ]
                ].rename(
                    columns={
                        "unit_price": "contract_unit_price",
                    }
                ),
                on="vendor_id",
                how="left",
            )

            merged["invoice_unit_price"] = _numeric(
                merged,
                "unit_price",
            )

            merged["contract_unit_price"] = _numeric(
                merged,
                "contract_unit_price",
            )

            merged["quantity_num"] = _numeric(
                merged,
                "quantity",
            )

            merged["price_difference"] = (
                merged["invoice_unit_price"]
                - merged["contract_unit_price"]
            )

            merged["leakage"] = (
                merged["price_difference"]
                * merged["quantity_num"]
            )

            violations = merged[
                (merged["contract_unit_price"].notna())
                & (merged["price_difference"] > 0)
                & (merged["leakage"] > 0)
            ]

            for _, row in violations.iterrows():

                leakage = float(row["leakage"])

                results.append(
                    _base_claim(
                        claim_id=f"CLM-UPLOAD-CONTRACT-PRICE-{row['invoice_id']}",
                        leakage_type="CONTRACT_PRICE_MISMATCH",
                        vendor_id=str(row["vendor_id"]),
                        invoice_id=str(row["invoice_id"]),
                        sku=str(row["sku"]),
                        original_amount=float(
                            row["invoice_unit_price"]
                            * row["quantity_num"]
                        ),
                        expected_amount=float(
                            row["contract_unit_price"]
                            * row["quantity_num"]
                        ),
                        potential_leakage=leakage,
                        confidence_score=95.0,
                        evidence=(
                            f"Invoice price ₹{row['invoice_unit_price']:,.2f} "
                            f"exceeds contract price ₹{row['contract_unit_price']:,.2f}."
                        ),
                    )
                )

    return results


# ============================================================
# DUPLICATE PAYMENTS
# ============================================================

def detect_duplicate_payments(
    invoices: pd.DataFrame,
    payments: Optional[pd.DataFrame],
) -> list[dict]:

    results = []

    if payments is None or payments.empty:
        return results

    invoices = _clean_columns(invoices)
    payments = _clean_columns(payments)

    required_invoice = {
        "invoice_id",
        "invoice_amount",
    }

    required_payment = {
        "invoice_id",
        "paid_amount",
    }

    if not required_invoice.issubset(invoices.columns):
        return results

    if not required_payment.issubset(payments.columns):
        return results

    inv = invoices[
        [
            "invoice_id",
            "invoice_amount",
        ]
    ].drop_duplicates(
        subset=["invoice_id"]
    )

    pay = payments.copy()

    pay["paid_amount_num"] = _numeric(
        pay,
        "paid_amount",
    )

    grouped = (
        pay.groupby("invoice_id")
        .agg(
            payment_count=("paid_amount_num", "count"),
            total_paid=("paid_amount_num", "sum"),
        )
        .reset_index()
    )

    merged = inv.merge(
        grouped,
        on="invoice_id",
        how="inner",
    )

    merged["invoice_amount_num"] = _numeric(
        merged,
        "invoice_amount",
    )

    violations = merged[
        (
            (merged["payment_count"] > 1)
            | (
                merged["total_paid"]
                > merged["invoice_amount_num"]
            )
        )
        & (
            merged["total_paid"]
            > merged["invoice_amount_num"]
        )
    ]

    for _, row in violations.iterrows():

        leakage = float(
            row["total_paid"]
            - row["invoice_amount_num"]
        )

        results.append(
            _base_claim(
                claim_id=f"CLM-UPLOAD-DUPPAY-{row['invoice_id']}",
                leakage_type="DUPLICATE_PAYMENT",
                invoice_id=str(row["invoice_id"]),
                original_amount=float(row["invoice_amount_num"]),
                expected_amount=float(row["invoice_amount_num"]),
                potential_leakage=leakage,
                confidence_score=99.0,
                evidence=(
                    f"{int(row['payment_count'])} payments found for invoice "
                    f"{row['invoice_id']}; total paid ₹{row['total_paid']:,.2f} "
                    f"vs invoice amount ₹{row['invoice_amount_num']:,.2f}."
                ),
            )
        )

    return results


# ============================================================
# QUANTITY MISMATCH
# ============================================================

def detect_quantity_mismatches(
    invoices: pd.DataFrame,
    purchase_orders: Optional[pd.DataFrame] = None,
    goods_receipts: Optional[pd.DataFrame] = None,
) -> list[dict]:

    results = []

    invoices = _clean_columns(invoices)

    if purchase_orders is None or purchase_orders.empty:
        return results

    purchase_orders = _clean_columns(purchase_orders)

    required_invoice = {
        "invoice_id",
        "po_id",
        "vendor_id",
        "sku",
        "quantity",
        "unit_price",
    }

    required_po = {
        "po_id",
        "vendor_id",
        "sku",
        "quantity",
    }

    if not required_invoice.issubset(invoices.columns):
        return results

    if not required_po.issubset(purchase_orders.columns):
        return results

    po = purchase_orders[
        [
            "po_id",
            "vendor_id",
            "sku",
            "quantity",
        ]
    ].rename(
        columns={
            "quantity": "po_quantity",
        }
    )

    merged = invoices.merge(
        po,
        on=["po_id", "vendor_id", "sku"],
        how="left",
    )

    merged["invoice_quantity"] = _numeric(
        merged,
        "quantity",
    )

    merged["po_quantity"] = _numeric(
        merged,
        "po_quantity",
    )

    merged["unit_price_num"] = _numeric(
        merged,
        "unit_price",
    )

    # PO-based quantity mismatch
    merged["excess_quantity"] = (
        merged["invoice_quantity"]
        - merged["po_quantity"]
    )

    # If goods receipts exist, use them as additional evidence.
    if goods_receipts is not None and not goods_receipts.empty:

        gr = _clean_columns(goods_receipts)

        if {
            "invoice_id",
            "received_quantity",
        }.issubset(gr.columns):

            gr_summary = (
                gr.groupby("invoice_id")[
                    "received_quantity"
                ]
                .sum()
                .reset_index()
                .rename(
                    columns={
                        "received_quantity": "received_quantity_total"
                    }
                )
            )

            merged = merged.merge(
                gr_summary,
                on="invoice_id",
                how="left",
            )

            merged["received_quantity_total"] = _numeric(
                merged,
                "received_quantity_total",
            )

            merged["excess_vs_receipt"] = (
                merged["invoice_quantity"]
                - merged["received_quantity_total"]
            )

            # Use the more conservative evidence boundary.
            merged["effective_excess"] = merged[
                [
                    "excess_quantity",
                    "excess_vs_receipt",
                ]
            ].min(axis=1)

        else:
            merged["effective_excess"] = merged[
                "excess_quantity"
            ]

    else:
        merged["effective_excess"] = merged[
            "excess_quantity"
        ]

    merged["leakage"] = (
        merged["effective_excess"]
        * merged["unit_price_num"]
    )

    violations = merged[
        (merged["effective_excess"] > 0)
        & (merged["unit_price_num"] > 0)
        & (merged["leakage"] > 0)
    ]

    for _, row in violations.iterrows():

        leakage = float(row["leakage"])

        results.append(
            _base_claim(
                claim_id=f"CLM-UPLOAD-QTY-{row['invoice_id']}",
                leakage_type="QUANTITY_MISMATCH",
                vendor_id=str(row["vendor_id"]),
                invoice_id=str(row["invoice_id"]),
                po_id=str(row["po_id"]),
                sku=str(row["sku"]),
                original_amount=float(
                    row["invoice_quantity"]
                    * row["unit_price_num"]
                ),
                expected_amount=float(
                    row["po_quantity"]
                    * row["unit_price_num"]
                ),
                potential_leakage=leakage,
                confidence_score=94.0,
                evidence=(
                    f"Invoice quantity={row['invoice_quantity']:,.0f}, "
                    f"PO quantity={row['po_quantity']:,.0f}; "
                    f"effective excess={row['effective_excess']:,.0f}."
                ),
            )
        )

    return results


# ============================================================
# MISSING REBATES
# ============================================================

def detect_missing_rebates(
    invoices: pd.DataFrame,
    contracts: Optional[pd.DataFrame] = None,
    rebates: Optional[pd.DataFrame] = None,
) -> list[dict]:

    results = []

    if contracts is None or contracts.empty:
        return results

    if rebates is None or rebates.empty:
        return results

    invoices = _clean_columns(invoices)
    contracts = _clean_columns(contracts)
    rebates = _clean_columns(rebates)

    if not {
        "invoice_id",
        "vendor_id",
        "invoice_amount",
    }.issubset(invoices.columns):
        return results

    if not {
        "vendor_id",
        "rebate_percentage",
    }.issubset(contracts.columns):
        return results

    if not {
        "invoice_id",
        "credited_rebate",
    }.issubset(rebates.columns):
        return results

    contract = contracts[
        [
            "vendor_id",
            "rebate_percentage",
        ]
    ].copy()

    contract["rebate_percentage_num"] = _numeric(
        contract,
        "rebate_percentage",
    )

    # Keep one contract rule per vendor for this uploaded-data demo.
    contract = contract.drop_duplicates(
        subset=["vendor_id"]
    )

    rb = rebates[
        [
            "invoice_id",
            "credited_rebate",
        ]
    ].copy()

    rb["credited_rebate_num"] = _numeric(
        rb,
        "credited_rebate",
    )

    rb = (
        rb.groupby("invoice_id")[
            "credited_rebate_num"
        ]
        .sum()
        .reset_index()
    )

    merged = invoices.merge(
        contract[
            [
                "vendor_id",
                "rebate_percentage_num",
            ]
        ],
        on="vendor_id",
        how="left",
    )

    merged = merged.merge(
        rb,
        on="invoice_id",
        how="left",
    )

    merged["invoice_amount_num"] = _numeric(
        merged,
        "invoice_amount",
    )

    merged["credited_rebate_num"] = merged[
        "credited_rebate_num"
    ].fillna(0)

    merged["expected_rebate"] = (
        merged["invoice_amount_num"]
        * merged["rebate_percentage_num"]
        / 100
    )

    merged["missing_rebate"] = (
        merged["expected_rebate"]
        - merged["credited_rebate_num"]
    )

    violations = merged[
        (merged["missing_rebate"] > 0)
        & (merged["rebate_percentage_num"] > 0)
    ]

    for _, row in violations.iterrows():

        leakage = float(row["missing_rebate"])

        results.append(
            _base_claim(
                claim_id=f"CLM-UPLOAD-REBATE-{row['invoice_id']}",
                leakage_type="MISSING_REBATE",
                vendor_id=str(row["vendor_id"]),
                invoice_id=str(row["invoice_id"]),
                original_amount=float(row["invoice_amount_num"]),
                expected_amount=float(row["expected_rebate"]),
                potential_leakage=leakage,
                confidence_score=92.0,
                evidence=(
                    f"Expected rebate ₹{row['expected_rebate']:,.2f}; "
                    f"credited ₹{row['credited_rebate_num']:,.2f}; "
                    f"missing ₹{leakage:,.2f}."
                ),
            )
        )

    return results


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_uploaded_analysis(
    workspace_path: str | Path,
) -> dict:

    workspace = Path(workspace_path)

    if not workspace.exists():
        raise FileNotFoundError(
            f"Upload workspace does not exist: {workspace}"
        )

    # --------------------------------------------------------
    # Load uploaded datasets
    # --------------------------------------------------------

    dataset_files = {}

    for dataset_type in [
        "invoices",
        "purchase_orders",
        "payments",
        "contracts",
        "rebates",
        "goods_receipts",
    ]:

        path = _find_dataset(
            workspace,
            dataset_type,
        )

        if path is not None:
            dataset_files[dataset_type] = path

    if "invoices" not in dataset_files:
        raise ValueError(
            "Invoices dataset is required before analysis can run."
        )

    invoices = _clean_columns(
        _read_csv(dataset_files["invoices"])
    )

    purchase_orders = (
        _clean_columns(
            _read_csv(dataset_files["purchase_orders"])
        )
        if "purchase_orders" in dataset_files
        else None
    )

    payments = (
        _clean_columns(
            _read_csv(dataset_files["payments"])
        )
        if "payments" in dataset_files
        else None
    )

    contracts = (
        _clean_columns(
            _read_csv(dataset_files["contracts"])
        )
        if "contracts" in dataset_files
        else None
    )

    rebates = (
        _clean_columns(
            _read_csv(dataset_files["rebates"])
        )
        if "rebates" in dataset_files
        else None
    )

    goods_receipts = (
        _clean_columns(
            _read_csv(dataset_files["goods_receipts"])
        )
        if "goods_receipts" in dataset_files
        else None
    )

    # --------------------------------------------------------
    # Run detectors
    # --------------------------------------------------------

    claims = []

    claims.extend(
        detect_price_mismatches(
            invoices=invoices,
            purchase_orders=purchase_orders,
            contracts=contracts,
        )
    )

    claims.extend(
        detect_duplicate_payments(
            invoices=invoices,
            payments=payments,
        )
    )

    claims.extend(
        detect_quantity_mismatches(
            invoices=invoices,
            purchase_orders=purchase_orders,
            goods_receipts=goods_receipts,
        )
    )

    claims.extend(
        detect_missing_rebates(
            invoices=invoices,
            contracts=contracts,
            rebates=rebates,
        )
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results_dir = workspace / "results"
    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    claims_df = pd.DataFrame(claims)

    if claims_df.empty:

        claims_df = pd.DataFrame(
            columns=[
                "claim_id",
                "leakage_type",
                "vendor_id",
                "invoice_id",
                "po_id",
                "contract_id",
                "rebate_id",
                "sku",
                "original_amount",
                "expected_amount",
                "potential_leakage",
                "confidence_score",
                "risk_level",
                "currency",
                "evidence",
                "status",
                "detected_at",
                "engine_version",
            ]
        )

    # Remove accidental duplicates.
    claims_df = claims_df.drop_duplicates(
        subset=["claim_id"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save unified claims
    # --------------------------------------------------------

    claims_file = (
        results_dir
        / "uploaded_unified_claims.csv"
    )

    claims_df.to_csv(
        claims_file,
        index=False,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_claims = len(claims_df)

    potential_leakage = float(
        pd.to_numeric(
            claims_df["potential_leakage"],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )

    if total_claims > 0:

        leakage_by_type = (
            claims_df.groupby(
                "leakage_type"
            )["potential_leakage"]
            .sum()
            .sort_values(
                ascending=False
            )
            .to_dict()
        )

        risk_distribution = (
            claims_df["risk_level"]
            .value_counts()
            .to_dict()
        )

    else:

        leakage_by_type = {}
        risk_distribution = {}

    summary = {
        "analysis_status": "completed",
        "engine_version": ENGINE_VERSION,
        "workspace": str(workspace),
        "datasets_found": sorted(
            dataset_files.keys()
        ),
        "total_claims": total_claims,
        "potential_leakage": potential_leakage,
        "leakage_by_type": leakage_by_type,
        "risk_distribution": risk_distribution,
        "results_file": str(claims_file),
        "completed_at": datetime.utcnow().isoformat(),
    }

    # Save machine-readable summary.
    summary_file = (
        results_dir
        / "uploaded_analysis_summary.json"
    )

    import json

    with open(
        summary_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
            default=str,
        )

    return summary


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run DollarGuard AI leakage analysis "
            "on an uploaded-data workspace."
        )
    )

    parser.add_argument(
        "workspace",
        help="Path to uploaded session workspace.",
    )

    args = parser.parse_args()

    result = run_uploaded_analysis(
        args.workspace
    )

    print()
    print("=" * 60)
    print("DOLLARGUARD AI - UPLOADED DATA ANALYSIS")
    print("=" * 60)
    print(
        f"Status              : {result['analysis_status']}"
    )
    print(
        f"Datasets found      : {', '.join(result['datasets_found'])}"
    )
    print(
        f"Claims detected     : {result['total_claims']:,}"
    )
    print(
        f"Potential leakage   : ₹{result['potential_leakage']:,.2f}"
    )
    print()
    print("Leakage by type:")

    for key, value in result[
        "leakage_by_type"
    ].items():

        print(
            f"  {key:<25} ₹{value:,.2f}"
        )

    print()
    print("Risk distribution:")

    for key, value in result[
        "risk_distribution"
    ].items():

        print(
            f"  {key:<15} {value:,}"
        )

    print()
    print(
        f"Results saved to    : {result['results_file']}"
    )
    print("=" * 60)