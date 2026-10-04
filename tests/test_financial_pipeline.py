from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_processed(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename

    assert path.exists(), (
        f"Required output file is missing: {path}"
    )

    df = pd.read_csv(path)

    assert not df.empty, (
        f"Output file is empty: {path}"
    )

    return df


def test_unified_claims():
    df = load_processed("unified_claims.csv")

    required_columns = {
        "claim_id",
        "leakage_type",
        "vendor_id",
        "potential_leakage",
        "confidence_score",
        "risk_level",
        "status",
    }

    assert required_columns.issubset(df.columns)

    assert df["claim_id"].notna().all()
    assert df["vendor_id"].notna().all()

    assert (
        df["potential_leakage"] >= 0
    ).all()

    assert df["leakage_type"].notna().all()

    valid_risk_levels = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }

    assert set(
        df["risk_level"].dropna()
    ).issubset(valid_risk_levels)


def test_investigation_reports():
    df = load_processed(
        "investigation_reports.csv"
    )

    required_columns = {
        "investigation_id",
        "claim_id",
        "vendor_id",
        "potential_leakage",
        "investigation_priority",
        "root_cause",
        "recommended_recovery_action",
    }

    assert required_columns.issubset(
        df.columns
    )

    assert df["investigation_id"].notna().all()
    assert df["claim_id"].notna().all()

    assert (
        df["potential_leakage"] >= 0
    ).all()

    valid_priorities = {
        "P1",
        "P2",
        "P3",
        "P4",
    }

    assert set(
        df["investigation_priority"].dropna()
    ).issubset(valid_priorities)


def test_recovery_claims():
    df = load_processed(
        "recovery_claims.csv"
    )

    required_columns = {
        "recovery_claim_id",
        "investigation_id",
        "vendor_id",
        "potential_leakage",
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
        "claim_status",
        "recovery_priority",
    }

    assert required_columns.issubset(
        df.columns
    )

    assert df["recovery_claim_id"].notna().all()

    assert (
        df["potential_leakage"] >= 0
    ).all()

    assert (
        df["claimed_amount"] >= 0
    ).all()

    assert (
        df["recovered_amount"] >= 0
    ).all()

    assert (
        df["outstanding_amount"] >= 0
    ).all()

    calculated_outstanding = (
        df["claimed_amount"]
        - df["recovered_amount"]
    ).clip(lower=0)

    pd.testing.assert_series_equal(
        df["outstanding_amount"].round(2),
        calculated_outstanding.round(2),
        check_names=False,
    )

    valid_statuses = {
        "NEW",
        "UNDER_REVIEW",
        "CLAIM_RAISED",
        "RECOVERY_IN_PROGRESS",
        "RECOVERED",
        "REJECTED",
        "CLOSED",
    }

    assert set(
        df["claim_status"].dropna()
    ).issubset(valid_statuses)


def test_vendor_analytics():
    df = load_processed(
        "vendor_analytics.csv"
    )

    required_columns = {
        "vendor_id",
        "claim_count",
        "potential_leakage",
        "critical_claims",
        "high_claims",
        "vendor_risk_score",
        "vendor_risk_tier",
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
        "recovery_rate",
    }

    assert required_columns.issubset(
        df.columns
    )

    assert df["vendor_id"].notna().all()

    assert (
        df["claim_count"] >= 0
    ).all()

    assert (
        df["potential_leakage"] >= 0
    ).all()

    assert (
        df["critical_claims"] >= 0
    ).all()

    assert (
        df["high_claims"] >= 0
    ).all()

    assert df[
        "vendor_risk_score"
    ].between(0, 100).all()

    valid_tiers = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }

    assert set(
        df["vendor_risk_tier"].dropna()
    ).issubset(valid_tiers)

    assert (
        df["recovery_rate"] >= 0
    ).all()

    assert (
        df["recovery_rate"] <= 100
    ).all()


def test_investigation_packets():
    df = load_processed(
        "investigation_packets.csv"
    )

    required_columns = {
        "investigation_packet_id",
        "investigation_id",
        "claim_id",
        "vendor_id",
        "leakage_type",
        "risk_level",
        "investigation_priority",
        "potential_leakage",
        "evidence_coverage",
        "evidence_chain",
        "investigation_conclusion",
        "recommended_recovery_action",
        "packet_status",
    }

    assert required_columns.issubset(
        df.columns
    )

    assert (
        df["investigation_packet_id"]
        .notna()
        .all()
    )

    assert (
        df["investigation_id"]
        .notna()
        .all()
    )

    assert (
        df["claim_id"]
        .notna()
        .all()
    )

    assert (
        df["potential_leakage"] >= 0
    ).all()

    assert df[
        "evidence_coverage"
    ].between(0, 100).all()

    valid_packet_statuses = {
        "READY_FOR_REVIEW",
        "REVIEW_REQUIRED",
        "INSUFFICIENT_EVIDENCE",
    }

    assert set(
        df["packet_status"].dropna()
    ).issubset(valid_packet_statuses)


def test_recovery_analytics():
    df = load_processed(
        "recovery_analytics.csv"
    )

    # The recovery analytics service produces
    # dimensional analytics rather than a simple
    # metric/value key-value table.
    required_columns = {
        "analysis_dimension",
        "dimension_value",
        "claim_count",
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
        "recovery_rate",
        "average_confidence",
        "average_claim_age_days",
        "vendor_risk_tier",
        "vendor_risk_score",
    }

    assert required_columns.issubset(
        df.columns
    )

    assert (
        df["analysis_dimension"]
        .notna()
        .all()
    )

    assert (
        df["dimension_value"]
        .notna()
        .all()
    )

    assert (
        df["claim_count"] >= 0
    ).all()

    assert (
        df["claimed_amount"] >= 0
    ).all()

    assert (
        df["recovered_amount"] >= 0
    ).all()

    assert (
        df["outstanding_amount"] >= 0
    ).all()

    assert (
        df["recovery_rate"] >= 0
    ).all()

    assert (
        df["recovery_rate"] <= 100
    ).all()

    assert (
        df["average_confidence"] >= 0
    ).all()

    assert (
        df["average_confidence"] <= 100
    ).all()

    assert (
        df["average_claim_age_days"] >= 0
    ).all()

    assert (
        df["vendor_risk_score"] >= 0
    ).all()

    assert (
        df["vendor_risk_score"] <= 100
    ).all()


def test_cross_pipeline_claim_counts():
    unified = load_processed(
        "unified_claims.csv"
    )

    investigations = load_processed(
        "investigation_reports.csv"
    )

    recovery = load_processed(
        "recovery_claims.csv"
    )

    assert len(unified) > 0
    assert len(investigations) > 0
    assert len(recovery) > 0

    assert (
        len(investigations)
        >= len(unified)
    )

    assert (
        len(recovery)
        >= len(investigations)
    )


def test_recovery_amount_consistency():
    df = load_processed(
        "recovery_claims.csv"
    )

    expected_outstanding = (
        df["claimed_amount"]
        - df["recovered_amount"]
    ).clip(lower=0)

    difference = (
        df["outstanding_amount"]
        - expected_outstanding
    ).abs()

    assert (
        difference <= 0.01
    ).all()