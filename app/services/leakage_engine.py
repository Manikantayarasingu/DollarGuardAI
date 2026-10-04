"""
DollarGuard AI - Unified Leakage Detection Engine

Runs all deterministic revenue leakage detectors and combines
their results into one unified claims dataset.

Detectors:

1. Price Mismatch
2. Duplicate Payment
3. Quantity Mismatch
4. Missing Rebate

The unified engine provides a common interface for the future:

    Dashboard
        ↓
    Leakage Engine
        ↓
    Claim Management
        ↓
    AI Investigator
        ↓
    Recovery Workflow
"""

from datetime import datetime

import pandas as pd


# ============================================================
# DETECTOR IMPORTS
# ============================================================

from app.services.detectors.price_mismatch import (
    detect_price_mismatches,
)

from app.services.detectors.duplicate_payment import (
    detect_duplicate_payments,
)

from app.services.detectors.quantity_mismatch import (
    detect_quantity_mismatches,
)

from app.services.detectors.missing_rebate import (
    detect_missing_rebates,
)


# ============================================================
# CONSTANTS
# ============================================================

ENGINE_VERSION = "1.0.0"


LEAKAGE_TYPES = [
    "PRICE_MISMATCH",
    "DUPLICATE_PAYMENT",
    "QUANTITY_MISMATCH",
    "MISSING_REBATE",
]


# ============================================================
# EMPTY RESULT
# ============================================================

def empty_claim_dataset() -> pd.DataFrame:
    """
    Return an empty unified claims DataFrame.
    """

    return pd.DataFrame(
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


# ============================================================
# NORMALIZE DETECTOR RESULT
# ============================================================

def normalize_claims(
    claims: pd.DataFrame,
    leakage_type: str,
) -> pd.DataFrame:
    """
    Convert a detector-specific result into the common
    DollarGuard AI claim schema.
    """

    if claims is None or claims.empty:
        return empty_claim_dataset()

    result = claims.copy()

    # ---------------------------------------------------------
    # Ensure leakage type
    # ---------------------------------------------------------

    if "leakage_type" not in result.columns:

        result["leakage_type"] = leakage_type

    else:

        result["leakage_type"] = (
            result["leakage_type"]
            .fillna(leakage_type)
        )

    # ---------------------------------------------------------
    # Common columns
    # ---------------------------------------------------------

    common_columns = [
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
    ]

    # ---------------------------------------------------------
    # Create missing columns
    # ---------------------------------------------------------

    for column in common_columns:

        if column not in result.columns:

            result[column] = None

    # ---------------------------------------------------------
    # Add engine metadata
    # ---------------------------------------------------------

    result["engine_version"] = ENGINE_VERSION

    # ---------------------------------------------------------
    # Keep common schema
    # ---------------------------------------------------------

    result = result[
        common_columns
        + ["engine_version"]
    ].copy()

    return result


# ============================================================
# RUN PRICE MISMATCH
# ============================================================

def run_price_mismatch_detector() -> pd.DataFrame:
    """
    Run the price mismatch detector safely.
    """

    print(
        "\n[1/4] Running Price Mismatch Detector..."
    )

    try:

        claims = detect_price_mismatches()

        result = normalize_claims(
            claims,
            "PRICE_MISMATCH",
        )

        print(
            f"      Claims detected: "
            f"{len(result):,}"
        )

        return result

    except Exception as error:

        print(
            "      ERROR in Price Mismatch Detector:"
        )

        print(
            f"      {error}"
        )

        return empty_claim_dataset()


# ============================================================
# RUN DUPLICATE PAYMENT
# ============================================================

def run_duplicate_payment_detector() -> pd.DataFrame:
    """
    Run the duplicate payment detector safely.
    """

    print(
        "\n[2/4] Running Duplicate Payment Detector..."
    )

    try:

        claims = detect_duplicate_payments()

        result = normalize_claims(
            claims,
            "DUPLICATE_PAYMENT",
        )

        print(
            f"      Claims detected: "
            f"{len(result):,}"
        )

        return result

    except Exception as error:

        print(
            "      ERROR in Duplicate Payment Detector:"
        )

        print(
            f"      {error}"
        )

        return empty_claim_dataset()


# ============================================================
# RUN QUANTITY MISMATCH
# ============================================================

def run_quantity_mismatch_detector() -> pd.DataFrame:
    """
    Run the quantity mismatch detector safely.
    """

    print(
        "\n[3/4] Running Quantity Mismatch Detector..."
    )

    try:

        claims = detect_quantity_mismatches()

        result = normalize_claims(
            claims,
            "QUANTITY_MISMATCH",
        )

        print(
            f"      Claims detected: "
            f"{len(result):,}"
        )

        return result

    except Exception as error:

        print(
            "      ERROR in Quantity Mismatch Detector:"
        )

        print(
            f"      {error}"
        )

        return empty_claim_dataset()


# ============================================================
# RUN MISSING REBATE
# ============================================================

def run_missing_rebate_detector() -> pd.DataFrame:
    """
    Run the missing rebate detector safely.
    """

    print(
        "\n[4/4] Running Missing Rebate Detector..."
    )

    try:

        claims = detect_missing_rebates()

        result = normalize_claims(
            claims,
            "MISSING_REBATE",
        )

        print(
            f"      Claims detected: "
            f"{len(result):,}"
        )

        return result

    except Exception as error:

        print(
            "      ERROR in Missing Rebate Detector:"
        )

        print(
            f"      {error}"
        )

        return empty_claim_dataset()


# ============================================================
# RUN ALL DETECTORS
# ============================================================

def run_all_detectors() -> pd.DataFrame:
    """
    Execute all available leakage detectors.

    Returns
    -------
    pandas.DataFrame
        Unified leakage claims dataset.
    """

    print("\n" + "=" * 75)

    print(
        "DOLLARGUARD AI - UNIFIED LEAKAGE DETECTION ENGINE"
    )

    print("=" * 75)

    print(
        f"\nEngine Version: {ENGINE_VERSION}"
    )

    start_time = datetime.utcnow()

    # ---------------------------------------------------------
    # Run detectors
    # ---------------------------------------------------------

    price_claims = (
        run_price_mismatch_detector()
    )

    duplicate_claims = (
        run_duplicate_payment_detector()
    )

    quantity_claims = (
        run_quantity_mismatch_detector()
    )

    rebate_claims = (
        run_missing_rebate_detector()
    )

    # ---------------------------------------------------------
    # Combine
    # ---------------------------------------------------------

    all_claims = pd.concat(
        [
            price_claims,
            duplicate_claims,
            quantity_claims,
            rebate_claims,
        ],
        ignore_index=True,
    )

    # ---------------------------------------------------------
    # Remove accidental duplicates
    # ---------------------------------------------------------

    if not all_claims.empty:

        all_claims = (
            all_claims
            .drop_duplicates(
                subset=["claim_id"],
                keep="first",
            )
            .copy()
        )

    # ---------------------------------------------------------
    # Sort by leakage
    # ---------------------------------------------------------

    if not all_claims.empty:

        all_claims[
            "potential_leakage"
        ] = pd.to_numeric(
            all_claims[
                "potential_leakage"
            ],
            errors="coerce",
        ).fillna(0)

        all_claims = (
            all_claims
            .sort_values(
                by="potential_leakage",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    end_time = datetime.utcnow()

    runtime_seconds = (
        end_time - start_time
    ).total_seconds()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "-" * 75)

    print(
        "UNIFIED DETECTION SUMMARY"
    )

    print("-" * 75)

    print(
        f"\nTotal claims detected : "
        f"{len(all_claims):,}"
    )

    if not all_claims.empty:

        total_leakage = (
            all_claims[
                "potential_leakage"
            ].sum()
        )

        print(
            f"Potential leakage     : "
            f"₹{total_leakage:,.2f}"
        )

        print(
            "\nLeakage by Type:"
        )

        type_summary = (
            all_claims
            .groupby(
                "leakage_type"
            )
            .agg(
                claims=(
                    "claim_id",
                    "count",
                ),
                leakage=(
                    "potential_leakage",
                    "sum",
                ),
            )
            .sort_values(
                by="leakage",
                ascending=False,
            )
        )

        for leakage_type, row in (
            type_summary.iterrows()
        ):

            print(
                f"  {leakage_type:<20}"
                f" {int(row['claims']):>6,} claims"
                f"  ₹{row['leakage']:>15,.2f}"
            )

        # -----------------------------------------------------
        # Risk summary
        # -----------------------------------------------------

        print(
            "\nRisk Distribution:"
        )

        risk_summary = (
            all_claims[
                "risk_level"
            ]
            .value_counts()
        )

        for risk_level, count in (
            risk_summary.items()
        ):

            print(
                f"  {risk_level:<10}: "
                f"{count:,}"
            )

    print(
        f"\nDetection runtime     : "
        f"{runtime_seconds:.2f} seconds"
    )

    print(
        "\n" + "=" * 75
    )

    return all_claims


# ============================================================
# SAVE UNIFIED CLAIMS
# ============================================================

def save_claims(
    claims: pd.DataFrame,
    output_path: str = (
        "data/processed/unified_claims.csv"
    ),
) -> str:
    """
    Save unified claims to CSV.
    """

    import os

    directory = os.path.dirname(
        output_path
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    claims.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    claims = run_all_detectors()

    output_file = save_claims(
        claims
    )

    print(
        f"\nUnified claims saved to:"
    )

    print(
        f"  {output_file}"
    )

    print(
        "\nDollarGuard AI leakage engine "
        "completed successfully."
    )