
"""
DollarGuard AI
Vendor Risk & Recovery Analytics

Step 19

Purpose:
    Build vendor-level financial intelligence from:

        - Unified leakage claims
        - AI investigation reports
        - Recovery claims

Output:
    data/processed/vendor_analytics.csv

Metrics:
    - Claim count
    - Potential leakage
    - Claimed recovery
    - Recovered amount
    - Outstanding recovery
    - Recovery rate
    - Average confidence
    - Critical claims
    - P1 investigations
    - Leakage types
    - Dominant leakage type
    - Vendor risk score
    - Vendor risk tier
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

CLAIMS_FILE = (
    PROCESSED_DIR / "unified_claims.csv"
)

INVESTIGATION_FILE = (
    PROCESSED_DIR / "investigation_reports.csv"
)

RECOVERY_FILE = (
    PROCESSED_DIR / "recovery_claims.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR / "vendor_analytics.csv"
)


# ============================================================
# HELPERS
# ============================================================

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


def safe_number(
    series
) -> pd.Series:

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)


def load_csv(
    path: Path
) -> pd.DataFrame:

    if not path.exists():

        return pd.DataFrame()

    try:

        dataframe = pd.read_csv(
            path
        )

        return normalize_columns(
            dataframe
        )

    except Exception as exc:

        print(
            f"Unable to load {path}: {exc}"
        )

        return pd.DataFrame()


# ============================================================
# PREPARE CLAIM DATA
# ============================================================

def prepare_claims(
    claims: pd.DataFrame
) -> pd.DataFrame:

    if claims.empty:

        return pd.DataFrame(
            columns=[
                "vendor_id",
                "claim_id",
                "potential_leakage",
                "confidence_score",
                "risk_level",
                "leakage_type",
            ]
        )

    required_defaults = {
        "vendor_id": "",
        "claim_id": "",
        "potential_leakage": 0,
        "confidence_score": 0,
        "risk_level": "LOW",
        "leakage_type": "OTHER",
    }

    for column, default in required_defaults.items():

        if column not in claims.columns:

            claims[column] = default

    claims["vendor_id"] = (
        claims["vendor_id"]
        .fillna("UNKNOWN")
        .astype(str)
    )

    claims["potential_leakage"] = safe_number(
        claims["potential_leakage"]
    )

    claims["confidence_score"] = safe_number(
        claims["confidence_score"]
    )

    claims["risk_level"] = (
        claims["risk_level"]
        .fillna("LOW")
        .astype(str)
        .str.upper()
    )

    claims["leakage_type"] = (
        claims["leakage_type"]
        .fillna("OTHER")
        .astype(str)
    )

    return claims


# ============================================================
# PREPARE INVESTIGATION DATA
# ============================================================

def prepare_investigations(
    investigations: pd.DataFrame
) -> pd.DataFrame:

    if investigations.empty:

        return pd.DataFrame(
            columns=[
                "vendor_id",
                "investigation_id",
                "investigation_priority",
            ]
        )

    defaults = {
        "vendor_id": "",
        "investigation_id": "",
        "investigation_priority": "P4",
    }

    for column, default in defaults.items():

        if column not in investigations.columns:

            investigations[column] = default

    investigations["vendor_id"] = (
        investigations["vendor_id"]
        .fillna("UNKNOWN")
        .astype(str)
    )

    investigations["investigation_priority"] = (
        investigations[
            "investigation_priority"
        ]
        .fillna("P4")
        .astype(str)
        .str.upper()
    )

    return investigations


# ============================================================
# PREPARE RECOVERY DATA
# ============================================================

def prepare_recovery(
    recovery: pd.DataFrame
) -> pd.DataFrame:

    if recovery.empty:

        return pd.DataFrame(
            columns=[
                "vendor_id",
                "recovery_claim_id",
                "claimed_amount",
                "recovered_amount",
                "outstanding_amount",
                "claim_status",
            ]
        )

    defaults = {
        "vendor_id": "UNKNOWN",
        "recovery_claim_id": "",
        "claimed_amount": 0,
        "recovered_amount": 0,
        "outstanding_amount": 0,
        "claim_status": "NEW",
    }

    for column, default in defaults.items():

        if column not in recovery.columns:

            recovery[column] = default

    recovery["vendor_id"] = (
        recovery["vendor_id"]
        .fillna("UNKNOWN")
        .astype(str)
    )

    for column in [
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
    ]:

        recovery[column] = safe_number(
            recovery[column]
        )

    recovery["claim_status"] = (
        recovery["claim_status"]
        .fillna("NEW")
        .astype(str)
        .str.upper()
    )

    return recovery


# ============================================================
# VENDOR RISK SCORE
# ============================================================

def calculate_vendor_risk_score(
    leakage: float,
    claim_count: int,
    critical_claims: int,
    p1_investigations: int,
    outstanding: float,
    average_confidence: float,
) -> float:

    score = 0.0

    # --------------------------------------------------------
    # Leakage exposure
    # --------------------------------------------------------

    if leakage >= 50_000_000:
        score += 35

    elif leakage >= 20_000_000:
        score += 28

    elif leakage >= 10_000_000:
        score += 20

    elif leakage >= 5_000_000:
        score += 12

    elif leakage >= 1_000_000:
        score += 6

    # --------------------------------------------------------
    # Claim volume
    # --------------------------------------------------------

    if claim_count >= 100:
        score += 20

    elif claim_count >= 50:
        score += 15

    elif claim_count >= 20:
        score += 10

    elif claim_count >= 10:
        score += 5

    # --------------------------------------------------------
    # Critical claims
    # --------------------------------------------------------

    if critical_claims >= 20:
        score += 15

    elif critical_claims >= 10:
        score += 12

    elif critical_claims >= 5:
        score += 8

    elif critical_claims >= 1:
        score += 4

    # --------------------------------------------------------
    # P1 investigations
    # --------------------------------------------------------

    if p1_investigations >= 20:
        score += 15

    elif p1_investigations >= 10:
        score += 12

    elif p1_investigations >= 5:
        score += 8

    elif p1_investigations >= 1:
        score += 4

    # --------------------------------------------------------
    # Outstanding recovery
    # --------------------------------------------------------

    if outstanding >= 50_000_000:
        score += 10

    elif outstanding >= 20_000_000:
        score += 8

    elif outstanding >= 10_000_000:
        score += 5

    elif outstanding >= 1_000_000:
        score += 2

    # --------------------------------------------------------
    # Confidence adjustment
    # --------------------------------------------------------

    if average_confidence >= 95:

        score += 5

    elif average_confidence >= 90:

        score += 3

    # --------------------------------------------------------
    # Cap
    # --------------------------------------------------------

    return min(
        round(score, 2),
        100.0
    )


# ============================================================
# RISK TIER
# ============================================================

def determine_risk_tier(
    score: float
) -> str:

    if score >= 75:

        return "CRITICAL"

    if score >= 50:

        return "HIGH"

    if score >= 25:

        return "MEDIUM"

    return "LOW"


# ============================================================
# DOMINANT LEAKAGE TYPE
# ============================================================

def dominant_leakage_type(
    dataframe: pd.DataFrame
) -> str:

    if dataframe.empty:

        return "NONE"

    if "leakage_type" not in dataframe.columns:

        return "UNKNOWN"

    counts = (
        dataframe[
            "leakage_type"
        ]
        .astype(str)
        .value_counts()
    )

    if counts.empty:

        return "NONE"

    return str(
        counts.index[0]
    )


# ============================================================
# BUILD VENDOR ANALYTICS
# ============================================================

def build_vendor_analytics(
    claims: pd.DataFrame,
    investigations: pd.DataFrame,
    recovery: pd.DataFrame,
) -> pd.DataFrame:

    claims = prepare_claims(
        claims
    )

    investigations = prepare_investigations(
        investigations
    )

    recovery = prepare_recovery(
        recovery
    )

    # --------------------------------------------------------
    # Vendor universe
    # --------------------------------------------------------

    vendors = set()

    if not claims.empty:

        vendors.update(
            claims["vendor_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

    if not investigations.empty:

        vendors.update(
            investigations["vendor_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

    if not recovery.empty:

        vendors.update(
            recovery["vendor_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

    vendors = sorted(
        vendor
        for vendor in vendors
        if vendor
    )

    results = []

    print(
        f"Building analytics for "
        f"{len(vendors):,} vendors..."
    )

    # --------------------------------------------------------
    # Vendor aggregation
    # --------------------------------------------------------

    for vendor_id in vendors:

        vendor_claims = claims[
            claims["vendor_id"]
            == vendor_id
        ]

        vendor_investigations = (
            investigations[
                investigations["vendor_id"]
                == vendor_id
            ]
        )

        vendor_recovery = recovery[
            recovery["vendor_id"]
            == vendor_id
        ]

        claim_count = len(
            vendor_claims
        )

        leakage = (
            safe_number(
                vendor_claims[
                    "potential_leakage"
                ]
            ).sum()
        )

        critical_claims = int(
            (
                vendor_claims[
                    "risk_level"
                ]
                == "CRITICAL"
            ).sum()
        )

        high_claims = int(
            (
                vendor_claims[
                    "risk_level"
                ]
                == "HIGH"
            ).sum()
        )

        average_confidence = (
            safe_number(
                vendor_claims[
                    "confidence_score"
                ]
            ).mean()
            if claim_count
            else 0
        )

        p1_investigations = int(
            (
                vendor_investigations[
                    "investigation_priority"
                ]
                == "P1"
            ).sum()
        )

        p2_investigations = int(
            (
                vendor_investigations[
                    "investigation_priority"
                ]
                == "P2"
            ).sum()
        )

        claimed_amount = (
            safe_number(
                vendor_recovery[
                    "claimed_amount"
                ]
            ).sum()
        )

        recovered_amount = (
            safe_number(
                vendor_recovery[
                    "recovered_amount"
                ]
            ).sum()
        )

        outstanding_amount = (
            safe_number(
                vendor_recovery[
                    "outstanding_amount"
                ]
            ).sum()
        )

        recovery_rate = (
            recovered_amount
            / claimed_amount
            * 100
            if claimed_amount > 0
            else 0
        )

        recovered_claims = int(
            (
                vendor_recovery[
                    "claim_status"
                ]
                == "RECOVERED"
            ).sum()
        )

        risk_score = (
            calculate_vendor_risk_score(
                leakage=leakage,
                claim_count=claim_count,
                critical_claims=critical_claims,
                p1_investigations=p1_investigations,
                outstanding=outstanding_amount,
                average_confidence=average_confidence,
            )
        )

        risk_tier = determine_risk_tier(
            risk_score
        )

        dominant_type = (
            dominant_leakage_type(
                vendor_claims
            )
        )

        leakage_types = (
            ", ".join(
                sorted(
                    vendor_claims[
                        "leakage_type"
                    ]
                    .astype(str)
                    .unique()
                    .tolist()
                )
            )
            if not vendor_claims.empty
            else "NONE"
        )

        results.append(
            {
                "vendor_id":
                    vendor_id,

                "claim_count":
                    claim_count,

                "potential_leakage":
                    leakage,

                "critical_claims":
                    critical_claims,

                "high_claims":
                    high_claims,

                "average_confidence":
                    round(
                        average_confidence,
                        2
                    ),

                "p1_investigations":
                    p1_investigations,

                "p2_investigations":
                    p2_investigations,

                "claimed_amount":
                    claimed_amount,

                "recovered_amount":
                    recovered_amount,

                "outstanding_amount":
                    outstanding_amount,

                "recovery_rate":
                    round(
                        recovery_rate,
                        2
                    ),

                "recovered_claims":
                    recovered_claims,

                "dominant_leakage_type":
                    dominant_type,

                "leakage_types":
                    leakage_types,

                "vendor_risk_score":
                    risk_score,

                "vendor_risk_tier":
                    risk_tier,
            }
        )

    result = pd.DataFrame(
        results
    )

    if not result.empty:

        result = result.sort_values(
            [
                "vendor_risk_score",
                "potential_leakage",
            ],
            ascending=[
                False,
                False,
            ]
        ).reset_index(
            drop=True
        )

    return result


# ============================================================
# SAVE
# ============================================================

def save_vendor_analytics(
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
# PRINT SUMMARY
# ============================================================

def print_summary(
    dataframe: pd.DataFrame
) -> None:

    print()

    print("=" * 70)

    print(
        "DOLLARGUARD AI - VENDOR ANALYTICS COMPLETE"
    )

    print("=" * 70)

    print()

    if dataframe.empty:

        print(
            "No vendor analytics generated."
        )

        return

    print(
        f"Vendors analyzed       : "
        f"{len(dataframe):,}"
    )

    print()

    print(
        "Risk Tier Distribution:"
    )

    tiers = (
        dataframe[
            "vendor_risk_tier"
        ]
        .value_counts()
    )

    for tier in [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]:

        print(
            f"  {tier:<10}: "
            f"{tiers.get(tier, 0):,}"
        )

    print()

    print(
        "Total Potential Leakage:"
    )

    print(
        f"  ₹{dataframe['potential_leakage'].sum():,.2f}"
    )

    print()

    print(
        "Total Outstanding Recovery:"
    )

    print(
        f"  ₹{dataframe['outstanding_amount'].sum():,.2f}"
    )

    print()

    print(
        "Top 10 Vendor Risk Exposure:"
    )

    display_columns = [
        "vendor_id",
        "claim_count",
        "potential_leakage",
        "outstanding_amount",
        "critical_claims",
        "p1_investigations",
        "vendor_risk_score",
        "vendor_risk_tier",
    ]

    top = (
        dataframe[
            display_columns
        ]
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

def run_vendor_analytics():

    print()

    print("=" * 70)

    print(
        "DOLLARGUARD AI - VENDOR ANALYTICS"
    )

    print("=" * 70)

    print()

    claims = load_csv(
        CLAIMS_FILE
    )

    investigations = load_csv(
        INVESTIGATION_FILE
    )

    recovery = load_csv(
        RECOVERY_FILE
    )

    if (
        claims.empty
        and investigations.empty
        and recovery.empty
    ):

        print(
            "No source data available."
        )

        print()

        print(
            "Run the leakage engine, "
            "AI Investigator, and "
            "Claim Management first."
        )

        return pd.DataFrame()

    dataframe = build_vendor_analytics(
        claims=claims,
        investigations=investigations,
        recovery=recovery,
    )

    save_vendor_analytics(
        dataframe
    )

    print_summary(
        dataframe
    )

    return dataframe


if __name__ == "__main__":

    run_vendor_analytics()
