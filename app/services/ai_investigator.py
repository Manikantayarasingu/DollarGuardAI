"""
DollarGuard AI
AI Investigator

Purpose:
    Convert detected revenue leakage claims into
    explainable investigation reports.

The investigator:
    - Reads unified leakage claims
    - Reads contract compliance findings
    - Builds evidence
    - Determines root cause
    - Estimates financial impact
    - Generates recovery recommendations
    - Assigns investigation priority
    - Produces a structured investigation report

Output:
    data/processed/investigation_reports.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

UNIFIED_CLAIMS_FILE = (
    PROCESSED_DIR
    / "unified_claims.csv"
)

CONTRACT_COMPLIANCE_FILE = (
    PROCESSED_DIR
    / "contract_compliance.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR
    / "investigation_reports.csv"
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(
    value,
    default: float = 0.0
) -> float:
    """
    Safely convert a value to float.
    """

    try:

        if pd.isna(value):
            return default

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except (
        ValueError,
        TypeError
    ):

        return default


def safe_text(
    value,
    default: str = ""
) -> str:
    """
    Safely convert a value to text.
    """

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
    """
    Normalize DataFrame column names.
    """

    dataframe = dataframe.copy()

    dataframe.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in dataframe.columns
    ]

    return dataframe


def load_optional_csv(
    path: Path
) -> pd.DataFrame:
    """
    Load a CSV if it exists.
    """

    if not path.exists():
        return pd.DataFrame()

    dataframe = pd.read_csv(
        path
    )

    return normalize_columns(
        dataframe
    )


# ============================================================
# INVESTIGATION CLASSIFICATION
# ============================================================

def classify_claim_type(
    leakage_type: str
) -> str:
    """
    Convert detection types into investigation categories.
    """

    value = (
        safe_text(
            leakage_type
        )
        .upper()
    )

    if "PRICE" in value:
        return "PRICING"

    if "DUPLICATE" in value:
        return "DUPLICATE_TRANSACTION"

    if "QUANTITY" in value:
        return "QUANTITY"

    if "REBATE" in value:
        return "REBATE"

    if "CONTRACT" in value:
        return "CONTRACT_COMPLIANCE"

    if "PAYMENT" in value:
        return "PAYMENT_COMPLIANCE"

    return "OTHER"


# ============================================================
# ROOT CAUSE
# ============================================================

def determine_root_cause(
    claim_type: str
) -> str:
    """
    Determine a concise root-cause category.
    """

    category = classify_claim_type(
        claim_type
    )

    causes = {
        "PRICING":
            (
                "Invoice pricing appears inconsistent "
                "with the expected purchase or contract price."
            ),

        "DUPLICATE_TRANSACTION":
            (
                "Multiple payment transactions appear "
                "to reference the same financial obligation."
            ),

        "QUANTITY":
            (
                "Invoice quantity appears inconsistent "
                "with the quantity supported by receiving records."
            ),

        "REBATE":
            (
                "Expected supplier rebate appears "
                "to exceed the rebate actually credited."
            ),

        "CONTRACT_COMPLIANCE":
            (
                "Transaction terms appear inconsistent "
                "with extracted contractual obligations."
            ),

        "PAYMENT_COMPLIANCE":
            (
                "Payment timing appears inconsistent "
                "with contractual payment terms."
            ),

        "OTHER":
            (
                "The transaction requires additional "
                "financial review."
            ),
    }

    return causes.get(
        category,
        causes["OTHER"]
    )


# ============================================================
# RECOVERY ACTION
# ============================================================

def determine_recovery_action(
    claim_type: str,
    potential_leakage: float
) -> str:
    """
    Recommend an investigation/recovery action.

    This is an operational recommendation,
    not a financial or legal conclusion.
    """

    category = classify_claim_type(
        claim_type
    )

    if category == "PRICING":

        return (
            "Validate contracted pricing, compare "
            "supporting purchase orders, and raise a "
            "supplier price-adjustment or credit-note request "
            "if the variance is confirmed."
        )

    if category == "DUPLICATE_TRANSACTION":

        return (
            "Reconcile the related invoice and payment "
            "records, confirm duplicate settlement, and "
            "initiate recovery or payment reversal "
            "according to company controls."
        )

    if category == "QUANTITY":

        return (
            "Compare invoice quantities against purchase "
            "orders and goods-receipt records, then request "
            "an invoice correction or supplier credit "
            "where excess billing is confirmed."
        )

    if category == "REBATE":

        return (
            "Validate the contractual rebate calculation "
            "and supplier credit records, then initiate "
            "a rebate recovery claim for the confirmed "
            "shortfall."
        )

    if category == "CONTRACT_COMPLIANCE":

        return (
            "Review the relevant contract clause and "
            "transaction evidence with the procurement "
            "team before raising a supplier recovery claim."
        )

    if category == "PAYMENT_COMPLIANCE":

        return (
            "Review the payment schedule and contractual "
            "terms to determine whether the timing created "
            "a recoverable financial impact."
        )

    return (
        "Perform manual financial review and validate "
        "supporting transaction evidence."
    )


# ============================================================
# INVESTIGATION PRIORITY
# ============================================================

def determine_priority(
    risk_level: str,
    potential_leakage: float,
    confidence_score: float
) -> str:
    """
    Assign an investigation priority.

    Priority is based on:
        - financial exposure
        - detection risk
        - confidence
    """

    risk = (
        safe_text(
            risk_level
        )
        .upper()
    )

    if (
        risk == "CRITICAL"
        or potential_leakage >= 5_000_000
    ):

        return "P1"

    if (
        risk == "HIGH"
        or potential_leakage >= 1_000_000
    ):

        return "P2"

    if (
        confidence_score >= 90
        and potential_leakage >= 100_000
    ):

        return "P3"

    return "P4"


# ============================================================
# INVESTIGATION SUMMARY
# ============================================================

def generate_investigation_summary(
    claim_type: str,
    vendor_id: str,
    invoice_id: str,
    potential_leakage: float,
    confidence_score: float,
    evidence: str
) -> str:
    """
    Generate a concise investigation narrative.
    """

    category = classify_claim_type(
        claim_type
    )

    vendor_text = (
        vendor_id
        if vendor_id
        else "the supplier"
    )

    invoice_text = (
        invoice_id
        if invoice_id
        else "the related transaction"
    )

    evidence_text = (
        evidence
        if evidence
        else "Automated transaction analysis identified a variance."
    )

    return (
        f"DollarGuard AI identified a {category.lower()} "
        f"anomaly involving {vendor_text} and "
        f"{invoice_text}. Estimated potential financial "
        f"exposure is ₹{potential_leakage:,.2f}, with a "
        f"detection confidence of {confidence_score:.1f}%. "
        f"Evidence: {evidence_text}"
    )


# ============================================================
# EVIDENCE QUALITY
# ============================================================

def determine_evidence_quality(
    evidence: str,
    confidence_score: float
) -> str:
    """
    Determine whether sufficient evidence exists
    for an initial investigation.
    """

    evidence_length = len(
        safe_text(
            evidence
        )
    )

    if (
        confidence_score >= 90
        and evidence_length >= 80
    ):

        return "STRONG"

    if (
        confidence_score >= 70
        and evidence_length >= 40
    ):

        return "MODERATE"

    return "LIMITED"


# ============================================================
# SINGLE CLAIM INVESTIGATION
# ============================================================

def investigate_claim(
    claim: pd.Series,
    source: str = "LEAKAGE_ENGINE"
) -> dict:
    """
    Build a complete investigation report for one claim.
    """

    claim_id = safe_text(
        claim.get(
            "claim_id"
        )
    )

    leakage_type = safe_text(
        claim.get(
            "leakage_type"
        ),
        "UNKNOWN"
    )

    vendor_id = safe_text(
        claim.get(
            "vendor_id"
        )
    )

    invoice_id = safe_text(
        claim.get(
            "invoice_id"
        )
    )

    po_id = safe_text(
        claim.get(
            "po_id"
        )
    )

    contract_id = safe_text(
        claim.get(
            "contract_id"
        )
    )

    sku = safe_text(
        claim.get(
            "sku"
        )
    )

    potential_leakage = safe_float(
        claim.get(
            "potential_leakage"
        )
    )

    confidence_score = safe_float(
        claim.get(
            "confidence_score"
        )
    )

    risk_level = safe_text(
        claim.get(
            "risk_level"
        ),
        "LOW"
    )

    evidence = safe_text(
        claim.get(
            "evidence"
        )
    )

    category = classify_claim_type(
        leakage_type
    )

    root_cause = determine_root_cause(
        leakage_type
    )

    recovery_action = determine_recovery_action(
        leakage_type,
        potential_leakage
    )

    priority = determine_priority(
        risk_level,
        potential_leakage,
        confidence_score
    )

    evidence_quality = (
        determine_evidence_quality(
            evidence,
            confidence_score
        )
    )

    summary = generate_investigation_summary(
        leakage_type,
        vendor_id,
        invoice_id,
        potential_leakage,
        confidence_score,
        evidence
    )

    return {
        "investigation_id":
            f"INV-{claim_id}",

        "claim_id":
            claim_id,

        "source":
            source,

        "investigation_category":
            category,

        "leakage_type":
            leakage_type,

        "vendor_id":
            vendor_id,

        "invoice_id":
            invoice_id,

        "po_id":
            po_id,

        "contract_id":
            contract_id,

        "sku":
            sku,

        "potential_leakage":
            potential_leakage,

        "confidence_score":
            confidence_score,

        "risk_level":
            risk_level,

        "investigation_priority":
            priority,

        "evidence_quality":
            evidence_quality,

        "root_cause":
            root_cause,

        "evidence":
            evidence,

        "investigation_summary":
            summary,

        "recommended_recovery_action":
            recovery_action,

        "recommended_next_step":
            (
                "Validate the identified evidence against "
                "the source financial records before "
                "initiating recovery."
            ),

        "investigation_status":
            "OPEN",

        "investigated_at":
            datetime.utcnow().isoformat(),

        "investigator_version":
            "1.0.0",
    }


# ============================================================
# INVESTIGATE UNIFIED CLAIMS
# ============================================================

def investigate_unified_claims() -> list[dict]:
    """
    Investigate claims generated by the leakage engine.
    """

    if not UNIFIED_CLAIMS_FILE.exists():

        print(
            "Unified claims file not found:"
        )

        print(
            f"  {UNIFIED_CLAIMS_FILE}"
        )

        print()

        print(
            "Run the leakage engine first:"
        )

        print(
            "python -m app.services.leakage_engine"
        )

        return []

    claims = pd.read_csv(
        UNIFIED_CLAIMS_FILE
    )

    claims = normalize_columns(
        claims
    )

    if claims.empty:
        return []

    results = []

    print(
        f"Investigating "
        f"{len(claims):,} unified claims..."
    )

    for _, claim in claims.iterrows():

        report = investigate_claim(
            claim,
            source="LEAKAGE_ENGINE"
        )

        results.append(
            report
        )

    return results


# ============================================================
# INVESTIGATE CONTRACT FINDINGS
# ============================================================

def investigate_contract_findings() -> list[dict]:
    """
    Investigate findings generated by the contract
    compliance engine.
    """

    if not CONTRACT_COMPLIANCE_FILE.exists():

        return []

    findings = pd.read_csv(
        CONTRACT_COMPLIANCE_FILE
    )

    findings = normalize_columns(
        findings
    )

    if findings.empty:
        return []

    results = []

    print(
        f"Investigating "
        f"{len(findings):,} contract findings..."
    )

    for _, finding in findings.iterrows():

        leakage_type = safe_text(
            finding.get(
                "compliance_type"
            ),
            "CONTRACT_COMPLIANCE"
        )

        converted_claim = pd.Series(
            {
                "claim_id":
                    finding.get(
                        "claim_id"
                    ),

                "leakage_type":
                    leakage_type,

                "vendor_id":
                    finding.get(
                        "vendor_id"
                    ),

                "invoice_id":
                    finding.get(
                        "invoice_id"
                    ),

                "po_id":
                    None,

                "contract_id":
                    finding.get(
                        "contract_id"
                    ),

                "sku":
                    None,

                "potential_leakage":
                    finding.get(
                        "potential_leakage"
                    ),

                "confidence_score":
                    finding.get(
                        "confidence_score"
                    ),

                "risk_level":
                    finding.get(
                        "risk_level"
                    ),

                "evidence":
                    finding.get(
                        "evidence"
                    ),
            }
        )

        report = investigate_claim(
            converted_claim,
            source="CONTRACT_COMPLIANCE"
        )

        results.append(
            report
        )

    return results


# ============================================================
# SAVE REPORTS
# ============================================================

def save_reports(
    reports: list[dict]
) -> pd.DataFrame:
    """
    Save investigation reports.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dataframe = pd.DataFrame(
        reports
    )

    if dataframe.empty:

        dataframe = pd.DataFrame(
            columns=[
                "investigation_id",
                "claim_id",
                "source",
                "investigation_category",
                "leakage_type",
                "vendor_id",
                "invoice_id",
                "po_id",
                "contract_id",
                "sku",
                "potential_leakage",
                "confidence_score",
                "risk_level",
                "investigation_priority",
                "evidence_quality",
                "root_cause",
                "evidence",
                "investigation_summary",
                "recommended_recovery_action",
                "recommended_next_step",
                "investigation_status",
                "investigated_at",
                "investigator_version",
            ]
        )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    return dataframe


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    dataframe: pd.DataFrame
):

    print()
    print("=" * 70)
    print(
        "DOLLARGUARD AI - "
        "AI INVESTIGATOR COMPLETE"
    )
    print("=" * 70)
    print()

    print(
        f"Investigation reports : "
        f"{len(dataframe):,}"
    )

    if dataframe.empty:

        print()
        print(
            "No investigation reports generated."
        )

        print()

        return

    leakage = pd.to_numeric(
        dataframe[
            "potential_leakage"
        ],
        errors="coerce"
    ).fillna(0)

    print(
        f"Potential exposure   : "
        f"₹{leakage.sum():,.2f}"
    )

    print()

    print(
        "Investigation Categories:"
    )

    categories = (
        dataframe[
            "investigation_category"
        ]
        .value_counts()
    )

    for category, count in categories.items():

        print(
            f"  {category:<30}"
            f"{count:,}"
        )

    print()

    print(
        "Investigation Priority:"
    )

    priorities = (
        dataframe[
            "investigation_priority"
        ]
        .value_counts()
    )

    for priority in [
        "P1",
        "P2",
        "P3",
        "P4",
    ]:

        print(
            f"  {priority:<5}: "
            f"{priorities.get(priority, 0):,}"
        )

    print()

    print(
        "Evidence Quality:"
    )

    evidence = (
        dataframe[
            "evidence_quality"
        ]
        .value_counts()
    )

    for quality in [
        "STRONG",
        "MODERATE",
        "LIMITED",
    ]:

        print(
            f"  {quality:<10}: "
            f"{evidence.get(quality, 0):,}"
        )

    print()

    print(
        "Top 10 Investigation Priorities:"
    )

    display_columns = [
        "investigation_id",
        "claim_id",
        "investigation_category",
        "vendor_id",
        "potential_leakage",
        "risk_level",
        "investigation_priority",
        "evidence_quality",
    ]

    available = [
        column
        for column in display_columns
        if column in dataframe.columns
    ]

    top = (
        dataframe[
            available
        ]
        .sort_values(
            [
                "potential_leakage"
            ],
            ascending=False
        )
        .head(10)
    )

    print(
        top.to_string(
            index=False
        )
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

def run_ai_investigator():

    print()
    print("=" * 70)
    print(
        "DOLLARGUARD AI - "
        "AI INVESTIGATOR"
    )
    print("=" * 70)
    print()

    reports = []

    # --------------------------------------------------------
    # UNIFIED CLAIMS
    # --------------------------------------------------------

    unified_reports = (
        investigate_unified_claims()
    )

    reports.extend(
        unified_reports
    )

    # --------------------------------------------------------
    # CONTRACT FINDINGS
    # --------------------------------------------------------

    contract_reports = (
        investigate_contract_findings()
    )

    reports.extend(
        contract_reports
    )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_reports = {}

    for report in reports:

        investigation_id = (
            report[
                "investigation_id"
            ]
        )

        unique_reports[
            investigation_id
        ] = report

    reports = list(
        unique_reports.values()
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    dataframe = save_reports(
        reports
    )

    print_summary(
        dataframe
    )

    return dataframe


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_ai_investigator()