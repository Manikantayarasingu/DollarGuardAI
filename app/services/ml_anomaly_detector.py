"""
DollarGuard AI - ML Anomaly Detection

Uses Isolation Forest to identify unusual invoice/payment
patterns that may represent previously unknown revenue leakage.

This complements the deterministic leakage detectors:

    Rule-Based Detection
            +
    ML Anomaly Detection
            =
    Broader Revenue Leakage Discovery
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT,
    )


# ============================================================
# DATABASE
# ============================================================

from app.database.connection import engine


# ============================================================
# CONSTANTS
# ============================================================

MODEL_VERSION = "1.0.0"

CONTAMINATION = 0.05

RANDOM_STATE = 42


# ============================================================
# LOAD TRANSACTION DATA
# ============================================================

def load_transaction_data() -> pd.DataFrame:
    """
    Load invoice-level financial transaction data and
    calculate behavioral features.
    """

    query = text(
        """
        SELECT

            i.invoice_id,
            i.po_id,
            i.vendor_id,
            i.sku,
            i.quantity,
            i.unit_price,
            i.invoice_amount,
            i.invoice_date,
            i.currency,

            po.quantity AS po_quantity,
            po.unit_price AS po_unit_price,
            po.po_amount,
            po.contract_id

        FROM invoices i

        LEFT JOIN purchase_orders po
            ON i.po_id = po.po_id
        """
    )

    with engine.connect() as connection:

        df = pd.read_sql_query(
            query,
            connection,
        )

    return df


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create numerical anomaly-detection features.
    """

    data = df.copy()

    numeric_columns = [
        "quantity",
        "unit_price",
        "invoice_amount",
        "po_quantity",
        "po_unit_price",
        "po_amount",
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

    # ---------------------------------------------------------
    # Price variance
    # ---------------------------------------------------------

    data["price_variance"] = (
        data["unit_price"]
        - data["po_unit_price"]
    )

    data["price_variance_pct"] = np.where(
        data["po_unit_price"] > 0,

        (
            data["price_variance"]
            / data["po_unit_price"]
        ) * 100,

        0,
    )

    # ---------------------------------------------------------
    # Quantity variance
    # ---------------------------------------------------------

    data["quantity_variance"] = (
        data["quantity"]
        - data["po_quantity"]
    )

    data["quantity_variance_pct"] = np.where(
        data["po_quantity"] > 0,

        (
            data["quantity_variance"]
            / data["po_quantity"]
        ) * 100,

        0,
    )

    # ---------------------------------------------------------
    # Invoice / PO amount ratio
    # ---------------------------------------------------------

    data["invoice_po_ratio"] = np.where(
        data["po_amount"] > 0,

        (
            data["invoice_amount"]
            / data["po_amount"]
        ),

        0,
    )

    # ---------------------------------------------------------
    # Vendor transaction frequency
    # ---------------------------------------------------------

    vendor_frequency = (
        data["vendor_id"]
        .value_counts()
        .rename(
            "vendor_invoice_count"
        )
    )

    data = data.merge(
        vendor_frequency,
        left_on="vendor_id",
        right_index=True,
        how="left",
    )

    # ---------------------------------------------------------
    # Vendor average invoice
    # ---------------------------------------------------------

    vendor_average = (
        data.groupby(
            "vendor_id"
        )[
            "invoice_amount"
        ]
        .mean()
        .rename(
            "vendor_average_invoice"
        )
    )

    data = data.merge(
        vendor_average,
        left_on="vendor_id",
        right_index=True,
        how="left",
    )

    # ---------------------------------------------------------
    # Difference from vendor average
    # ---------------------------------------------------------

    data["vendor_amount_deviation"] = np.where(
        data["vendor_average_invoice"] > 0,

        (
            data["invoice_amount"]
            - data["vendor_average_invoice"]
        )
        / data["vendor_average_invoice"]
        * 100,

        0,
    )

    # ---------------------------------------------------------
    # Log-scaled invoice amount
    # ---------------------------------------------------------

    data["log_invoice_amount"] = np.log1p(
        data["invoice_amount"].clip(
            lower=0
        )
    )

    return data


# ============================================================
# RUN MODEL
# ============================================================

def detect_anomalies(
    contamination: float = CONTAMINATION,
) -> pd.DataFrame:
    """
    Train Isolation Forest and return anomalous invoices.
    """

    print(
        "\nLoading transaction data..."
    )

    df = load_transaction_data()

    if df.empty:

        print(
            "No invoice data available."
        )

        return pd.DataFrame()

    print(
        f"Transactions loaded: "
        f"{len(df):,}"
    )

    # ---------------------------------------------------------
    # Feature engineering
    # ---------------------------------------------------------

    data = create_features(
        df
    )

    feature_columns = [
        "invoice_amount",
        "quantity",
        "unit_price",
        "po_quantity",
        "po_unit_price",
        "po_amount",
        "price_variance",
        "price_variance_pct",
        "quantity_variance",
        "quantity_variance_pct",
        "invoice_po_ratio",
        "vendor_invoice_count",
        "vendor_average_invoice",
        "vendor_amount_deviation",
        "log_invoice_amount",
    ]

    # ---------------------------------------------------------
    # Validate features
    # ---------------------------------------------------------

    available_features = [
        column
        for column in feature_columns
        if column in data.columns
    ]

    model_data = data[
        available_features
    ].copy()

    # ---------------------------------------------------------
    # Clean numerical values
    # ---------------------------------------------------------

    model_data = model_data.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    model_data = model_data.fillna(
        model_data.median(
            numeric_only=True
        )
    )

    model_data = model_data.fillna(0)

    # ---------------------------------------------------------
    # Train Isolation Forest
    # ---------------------------------------------------------

    print(
        "\nTraining Isolation Forest..."
    )

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    predictions = model.fit_predict(
        model_data
    )

    anomaly_scores = (
        model.decision_function(
            model_data
        )
    )

    # ---------------------------------------------------------
    # Store model output
    # ---------------------------------------------------------

    data["anomaly_prediction"] = (
        predictions
    )

    data["anomaly_score"] = (
        anomaly_scores
    )

    data["is_anomaly"] = (
        data["anomaly_prediction"]
        == -1
    )

    # ---------------------------------------------------------
    # Convert score to intuitive risk score
    # ---------------------------------------------------------

    score_min = (
        data["anomaly_score"].min()
    )

    score_max = (
        data["anomaly_score"].max()
    )

    if score_max != score_min:

        data["anomaly_risk_score"] = (
            100
            * (
                score_max
                - data["anomaly_score"]
            )
            / (
                score_max
                - score_min
            )
        )

    else:

        data["anomaly_risk_score"] = 0

    data["anomaly_risk_score"] = (
        data["anomaly_risk_score"]
        .clip(0, 100)
        .round(2)
    )

    # ---------------------------------------------------------
    # Risk classification
    # ---------------------------------------------------------

    def risk_level(score):

        if score >= 80:
            return "CRITICAL"

        if score >= 60:
            return "HIGH"

        if score >= 40:
            return "MEDIUM"

        return "LOW"

    data["anomaly_risk_level"] = (
        data["anomaly_risk_score"]
        .apply(risk_level)
    )

    # ---------------------------------------------------------
    # Detection reason
    # ---------------------------------------------------------

    def create_reason(row):

        reasons = []

        if abs(
            row["price_variance_pct"]
        ) >= 10:

            reasons.append(
                "unusual price variance"
            )

        if abs(
            row["quantity_variance_pct"]
        ) >= 10:

            reasons.append(
                "unusual quantity variance"
            )

        if (
            row["invoice_po_ratio"] >= 1.25
            or row["invoice_po_ratio"] <= 0.75
        ):

            reasons.append(
                "unusual invoice-to-PO ratio"
            )

        if (
            abs(
                row[
                    "vendor_amount_deviation"
                ]
            )
            >= 50
        ):

            reasons.append(
                "unusual vendor invoice amount"
            )

        if not reasons:

            reasons.append(
                "multivariate transaction anomaly"
            )

        return "; ".join(
            reasons
        )

    data["detection_reason"] = (
        data.apply(
            create_reason,
            axis=1,
        )
    )

    # ---------------------------------------------------------
    # Keep anomalies
    # ---------------------------------------------------------

    anomalies = data[
        data["is_anomaly"]
    ].copy()

    anomalies = anomalies.sort_values(
        by="anomaly_risk_score",
        ascending=False,
    ).reset_index(
        drop=True
    )

    return anomalies


# ============================================================
# SAVE RESULTS
# ============================================================

def save_anomalies(
    anomalies: pd.DataFrame,
) -> str:
    """
    Save anomaly results to processed data.
    """

    output_path = (
        "data/processed/"
        "ml_anomalies.csv"
    )

    os.makedirs(
        os.path.dirname(
            output_path
        ),
        exist_ok=True,
    )

    anomalies.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    anomalies: pd.DataFrame,
) -> None:
    """
    Print ML anomaly detection summary.
    """

    print(
        "\n" + "=" * 75
    )

    print(
        "DOLLARGUARD AI - ML ANOMALY DETECTION"
    )

    print(
        "=" * 75
    )

    if anomalies.empty:

        print(
            "\nNo anomalies detected."
        )

        print(
            "=" * 75
        )

        return

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    anomaly_count = len(
        anomalies
    )

    total_transactions = (
        load_transaction_data()
        .shape[0]
    )

    anomaly_rate = (
        anomaly_count
        / total_transactions
        * 100
        if total_transactions
        else 0
    )

    print(
        f"\nTransactions analyzed : "
        f"{total_transactions:,}"
    )

    print(
        f"Anomalies detected     : "
        f"{anomaly_count:,}"
    )

    print(
        f"Anomaly rate           : "
        f"{anomaly_rate:.2f}%"
    )

    # ---------------------------------------------------------
    # Risk distribution
    # ---------------------------------------------------------

    print(
        "\nML Risk Distribution:"
    )

    risk_counts = (
        anomalies[
            "anomaly_risk_level"
        ]
        .value_counts()
    )

    for risk_level, count in (
        risk_counts.items()
    ):

        print(
            f"  {risk_level:<10}: "
            f"{count:,}"
        )

    # ---------------------------------------------------------
    # Top anomalies
    # ---------------------------------------------------------

    print(
        "\nTop 10 ML Anomalies:"
    )

    display_columns = [
        "invoice_id",
        "vendor_id",
        "invoice_amount",
        "unit_price",
        "quantity",
        "anomaly_risk_score",
        "anomaly_risk_level",
        "detection_reason",
    ]

    print(
        anomalies[
            display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print(
        "\n" + "=" * 75
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    anomalies = detect_anomalies()

    print_summary(
        anomalies
    )

    if not anomalies.empty:

        output_file = save_anomalies(
            anomalies
        )

        print(
            f"\nML anomaly results saved to:"
        )

        print(
            f"  {output_file}"
        )

        print(
            f"\nModel version: "
            f"{MODEL_VERSION}"
        )