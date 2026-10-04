"""
DollarGuard AI - Executive Recovery Analytics
Builds management-level recovery analytics from recovery claims,
claims, investigations and vendor analytics.
"""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RECOVERY_FILE = PROCESSED_DIR / "recovery_claims.csv"
INVESTIGATION_FILE = PROCESSED_DIR / "investigation_reports.csv"
VENDOR_FILE = PROCESSED_DIR / "vendor_analytics.csv"
OUTPUT_FILE = PROCESSED_DIR / "recovery_analytics.csv"


def load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def num(df, col):
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def build_analytics():
    recovery = load_csv(RECOVERY_FILE)
    investigations = load_csv(INVESTIGATION_FILE)
    vendors = load_csv(VENDOR_FILE)

    if recovery.empty:
        print("No recovery claims found.")
        return pd.DataFrame()

    df = recovery.copy()
    for col in ["claimed_amount", "recovered_amount", "outstanding_amount", "confidence_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["recovery_rate"] = (df["recovered_amount"] / df["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    df["created_at"] = pd.to_datetime(df.get("created_at"), errors="coerce")
    today = pd.Timestamp.utcnow().tz_localize(None).normalize()
    df["claim_age_days"] = (today - df["created_at"].dt.tz_localize(None).dt.normalize()).dt.days.fillna(0).clip(lower=0)
    df["aging_bucket"] = pd.cut(
        df["claim_age_days"],
        bins=[-1, 7, 30, 60, 90, float("inf")],
        labels=["0-7 days", "8-30 days", "31-60 days", "61-90 days", "90+ days"],
    ).astype(str)

    if "claim_status" not in df.columns:
        df["claim_status"] = "NEW"
    if "recovery_priority" not in df.columns:
        df["recovery_priority"] = "NORMAL"
    if "recovery_category" not in df.columns:
        df["recovery_category"] = "GENERAL_RECOVERY"

    status = df.groupby("claim_status", dropna=False).agg(
        claim_count=("recovery_claim_id", "count"),
        claimed_amount=("claimed_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
    ).reset_index()
    status["recovery_rate"] = (status["recovered_amount"] / status["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    status["analysis_dimension"] = "STATUS"

    category = df.groupby("recovery_category", dropna=False).agg(
        claim_count=("recovery_claim_id", "count"),
        claimed_amount=("claimed_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
    ).reset_index().rename(columns={"recovery_category": "dimension_value"})
    category["recovery_rate"] = (category["recovered_amount"] / category["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    category["analysis_dimension"] = "RECOVERY_CATEGORY"

    priority = df.groupby("recovery_priority", dropna=False).agg(
        claim_count=("recovery_claim_id", "count"),
        claimed_amount=("claimed_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
    ).reset_index().rename(columns={"recovery_priority": "dimension_value"})
    priority["recovery_rate"] = (priority["recovered_amount"] / priority["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    priority["analysis_dimension"] = "PRIORITY"

    aging = df.groupby("aging_bucket", dropna=False).agg(
        claim_count=("recovery_claim_id", "count"),
        claimed_amount=("claimed_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
    ).reset_index().rename(columns={"aging_bucket": "dimension_value"})
    aging["recovery_rate"] = (aging["recovered_amount"] / aging["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    aging["analysis_dimension"] = "AGING"

    vendor = df.groupby("vendor_id", dropna=False).agg(
        claim_count=("recovery_claim_id", "count"),
        claimed_amount=("claimed_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
        average_confidence=("confidence_score", "mean"),
        average_claim_age_days=("claim_age_days", "mean"),
    ).reset_index()
    vendor["recovery_rate"] = (vendor["recovered_amount"] / vendor["claimed_amount"].replace(0, pd.NA) * 100).fillna(0.0)
    if not vendors.empty and "vendor_risk_tier" in vendors.columns:
        vendor = vendor.merge(vendors[["vendor_id", "vendor_risk_tier", "vendor_risk_score"]], on="vendor_id", how="left")
    vendor["analysis_dimension"] = "VENDOR"
    vendor["dimension_value"] = vendor["vendor_id"]

    rows = []
    for source in [status.rename(columns={"claim_status": "dimension_value"}), category, priority, aging, vendor]:
        for _, r in source.iterrows():
            rows.append({
                "analysis_dimension": r.get("analysis_dimension"),
                "dimension_value": r.get("dimension_value"),
                "claim_count": r.get("claim_count", 0),
                "claimed_amount": r.get("claimed_amount", 0),
                "recovered_amount": r.get("recovered_amount", 0),
                "outstanding_amount": r.get("outstanding_amount", 0),
                "recovery_rate": r.get("recovery_rate", 0),
                "average_confidence": r.get("average_confidence", 0),
                "average_claim_age_days": r.get("average_claim_age_days", 0),
                "vendor_risk_tier": r.get("vendor_risk_tier", ""),
                "vendor_risk_score": r.get("vendor_risk_score", 0),
            })

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT_FILE, index=False)

    print("=" * 70)
    print("DOLLARGUARD AI - EXECUTIVE RECOVERY ANALYTICS")
    print("=" * 70)
    print(f"Recovery claims analyzed : {len(df):,}")
    print(f"Claimed amount            : ₹{df['claimed_amount'].sum():,.2f}")
    print(f"Recovered amount          : ₹{df['recovered_amount'].sum():,.2f}")
    print(f"Outstanding amount        : ₹{df['outstanding_amount'].sum():,.2f}")
    print(f"Recovery rate             : {(df['recovered_amount'].sum()/df['claimed_amount'].sum()*100 if df['claimed_amount'].sum() else 0):.2f}%")
    print(f"Analytics records         : {len(result):,}")
    print("\nOutput file:")
    print(f"  {OUTPUT_FILE}")
    return result


if __name__ == "__main__":
    build_analytics()
