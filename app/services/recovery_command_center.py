from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RECOVERY_FILE = PROCESSED_DIR / "recovery_claims.csv"
PACKETS_FILE = PROCESSED_DIR / "investigation_packets.csv"
OUTPUT_FILE = PROCESSED_DIR / "recovery_command_center.csv"

STATUS_ORDER = {
    "NEW": 1,
    "UNDER_REVIEW": 2,
    "CLAIM_RAISED": 3,
    "RECOVERY_IN_PROGRESS": 4,
    "RECOVERED": 5,
    "REJECTED": 6,
    "CLOSED": 7,
}

PRIORITY_ORDER = {
    "URGENT": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "NORMAL": 4,
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def clean_text(value, default="") -> str:
    if pd.isna(value):
        return default
    return str(value).strip()


def next_action(row: pd.Series) -> str:
    status = clean_text(row.get("claim_status"), "NEW")
    response = clean_text(row.get("supplier_response"), "PENDING")
    outstanding = float(row.get("outstanding_amount", 0) or 0)
    evidence = float(row.get("evidence_coverage", 0) or 0)

    if status == "RECOVERED":
        return "Close recovery record and retain evidence."
    if status in {"REJECTED", "CLOSED"}:
        return "Review closure decision and supporting notes."
    if evidence < 70:
        return "Complete missing evidence before supplier escalation."
    if status == "NEW":
        return "Assign investigator and begin claim review."
    if status == "UNDER_REVIEW":
        return "Validate evidence and raise supplier claim."
    if status == "CLAIM_RAISED" and response == "PENDING":
        return "Follow up with supplier for response."
    if status == "CLAIM_RAISED" and response == "DISPUTED":
        return "Prepare dispute response using the evidence chain."
    if status == "CLAIM_RAISED":
        return "Move accepted claim into recovery execution."
    if status == "RECOVERY_IN_PROGRESS" and outstanding > 0:
        return "Track recovery payment and update recovered amount."
    return "Review claim and update next recovery action."


def build_command_center() -> pd.DataFrame:
    recovery = read_csv(RECOVERY_FILE)
    packets = read_csv(PACKETS_FILE)

    if recovery.empty:
        print("Recovery claims file is missing or empty.")
        return pd.DataFrame()

    if packets.empty:
        packets = pd.DataFrame(columns=["investigation_id"])

    if "investigation_id" in packets.columns:
        packet_columns = [
            "investigation_id",
            "investigation_packet_id",
            "leakage_type",
            "evidence_coverage",
            "evidence_chain",
            "investigation_conclusion",
            "recommended_recovery_action",
            "packet_status",
        ]
        packet_columns = [c for c in packet_columns if c in packets.columns]
        packets = packets[packet_columns].drop_duplicates("investigation_id")

        result = recovery.merge(
            packets,
            on="investigation_id",
            how="left",
            suffixes=("", "_packet"),
        )
    else:
        result = recovery.copy()

    for column in [
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
        "confidence_score",
        "evidence_coverage",
    ]:
        if column in result.columns:
            result[column] = number(result[column])

    if "claimed_amount" in result.columns and "recovered_amount" in result.columns:
        result["outstanding_amount"] = (
            result["claimed_amount"] - result["recovered_amount"]
        ).clip(lower=0)
        result["recovery_rate"] = (
            result["recovered_amount"]
            .div(result["claimed_amount"].replace(0, pd.NA))
            .fillna(0)
            * 100
        )
    else:
        result["recovery_rate"] = 0.0

    created = pd.to_datetime(
        result.get("created_at", pd.Series(index=result.index)),
        errors="coerce",
        utc=True,
    )
    now = pd.Timestamp.now(tz="UTC")
    result["aging_days"] = ((now - created).dt.total_seconds() / 86400).fillna(0).clip(lower=0).round(0).astype(int)

    result["status_rank"] = result.get("claim_status", "NEW").map(STATUS_ORDER).fillna(99)
    result["priority_rank"] = result.get("recovery_priority", "NORMAL").map(PRIORITY_ORDER).fillna(99)
    result["next_action"] = result.apply(next_action, axis=1)

    result["queue_score"] = (
        result["priority_rank"] * 100
        + result["status_rank"] * 10
        + (100 - result["evidence_coverage"].clip(0, 100)) * 0.1
    )

    sort_columns = [
        "priority_rank",
        "status_rank",
        "outstanding_amount",
    ]
    result = result.sort_values(
        sort_columns,
        ascending=[True, True, False],
    ).reset_index(drop=True)

    result.to_csv(OUTPUT_FILE, index=False)

    return result


def print_summary(df: pd.DataFrame) -> None:
    if df.empty:
        return

    claimed = number(df["claimed_amount"]).sum()
    recovered = number(df["recovered_amount"]).sum()
    outstanding = number(df["outstanding_amount"]).sum()
    rate = recovered / claimed * 100 if claimed else 0

    print("=" * 70)
    print("DOLLARGUARD AI - RECOVERY COMMAND CENTER")
    print("=" * 70)
    print(f"Recovery queue        : {len(df):,}")
    print(f"Claimed amount        : ₹{claimed:,.2f}")
    print(f"Recovered amount      : ₹{recovered:,.2f}")
    print(f"Outstanding amount    : ₹{outstanding:,.2f}")
    print(f"Recovery rate         : {rate:.2f}%")
    print()
    print("Status Distribution:")
    for status, count in df["claim_status"].value_counts().items():
        print(f"  {status:<24}: {count:,}")
    print()
    print("Priority Distribution:")
    for priority in ["URGENT", "HIGH", "MEDIUM", "NORMAL"]:
        count = int((df["recovery_priority"] == priority).sum())
        if count:
            print(f"  {priority:<10}: {count:,}")
    print()
    print(f"Output file:")
    print(f"  {OUTPUT_FILE}")


if __name__ == "__main__":
    dataframe = build_command_center()
    print_summary(dataframe)
