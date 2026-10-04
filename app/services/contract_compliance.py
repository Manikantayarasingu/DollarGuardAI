"""
DollarGuard AI
Contract-vs-Invoice Compliance Engine

Purpose:
    Compare extracted contract terms against enterprise
    financial transactions.

Detects:
    1. Contract price violations
    2. Contract rebate violations
    3. Payment-term violations

Output:
    data/processed/contract_compliance.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CONTRACT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "contract_intelligence.csv"
)

RAW_DATA_DIR = (
    BASE_DIR
    / "data"
    / "synthetic"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "contract_compliance.csv"
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a CSV file from the synthetic data directory.
    """

    path = RAW_DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required dataset not found:\n{path}"
        )

    dataframe = pd.read_csv(path)

    return normalize_columns(dataframe)


def normalize_columns(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize column names.
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


def first_existing_column(
    dataframe: pd.DataFrame,
    candidates: list[str]
) -> str | None:
    """
    Return the first matching column.
    """

    for column in candidates:

        if column in dataframe.columns:
            return column

    return None


def to_numeric(
    value
):
    """
    Safely convert a value to float.
    """

    try:

        if pd.isna(value):
            return None

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except (
        ValueError,
        TypeError
    ):

        return None


def numeric_series(
    series: pd.Series
) -> pd.Series:
    """
    Convert a pandas Series to numeric.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def risk_level(
    leakage: float
) -> str:
    """
    Assign risk based on potential financial exposure.
    """

    if leakage >= 5_000_000:
        return "CRITICAL"

    if leakage >= 1_000_000:
        return "HIGH"

    if leakage >= 100_000:
        return "MEDIUM"

    return "LOW"


# ============================================================
# CONTRACT LOADING
# ============================================================

def load_contracts() -> pd.DataFrame:
    """
    Load contract intelligence output.
    """

    if not CONTRACT_FILE.exists():

        raise FileNotFoundError(
            "contract_intelligence.csv was not found.\n\n"
            "Run Step 13 first:\n"
            "python -m app.services.contract_intelligence"
        )

    contracts = pd.read_csv(
        CONTRACT_FILE
    )

    contracts = normalize_columns(
        contracts
    )

    return contracts


# ============================================================
# CONTRACT PRICE COMPLIANCE
# ============================================================

def detect_price_violations(
    contracts: pd.DataFrame,
    invoices: pd.DataFrame
) -> list[dict]:
    """
    Compare contract unit prices with invoice unit prices.

    The function deliberately renames columns before joining
    to prevent Pandas merge suffix problems.
    """

    results = []

    if contracts.empty:
        return results

    if invoices.empty:
        return results

    # --------------------------------------------------------
    # CONTRACT COLUMNS
    # --------------------------------------------------------

    contract_vendor = first_existing_column(
        contracts,
        [
            "vendor_id",
            "vendor",
            "vendor_code",
        ]
    )

    contract_id = first_existing_column(
        contracts,
        [
            "contract_id",
        ]
    )

    contract_price = first_existing_column(
        contracts,
        [
            "unit_price",
            "contract_unit_price",
            "price_per_unit",
        ]
    )

    if not contract_vendor:
        print(
            "  Contract vendor column not found."
        )
        return results

    if not contract_price:
        print(
            "  Contract unit price column not found."
        )
        return results

    # --------------------------------------------------------
    # INVOICE COLUMNS
    # --------------------------------------------------------

    invoice_vendor = first_existing_column(
        invoices,
        [
            "vendor_id",
            "vendor",
            "vendor_code",
        ]
    )

    invoice_id = first_existing_column(
        invoices,
        [
            "invoice_id",
        ]
    )

    invoice_price = first_existing_column(
        invoices,
        [
            "unit_price",
            "invoice_unit_price",
            "price",
        ]
    )

    invoice_quantity = first_existing_column(
        invoices,
        [
            "quantity",
            "invoice_quantity",
            "invoiced_quantity",
        ]
    )

    if not invoice_vendor:
        print(
            "  Invoice vendor column not found."
        )
        return results

    if not invoice_id:
        print(
            "  Invoice ID column not found."
        )
        return results

    if not invoice_price:
        print(
            "  Invoice unit price column not found."
        )
        return results

    # --------------------------------------------------------
    # BUILD CLEAN CONTRACT TABLE
    # --------------------------------------------------------

    contract_columns = [
        contract_vendor,
        contract_price,
    ]

    if contract_id:
        contract_columns.append(
            contract_id
        )

    contract_data = contracts[
        contract_columns
    ].copy()

    rename_contract = {
        contract_vendor: "vendor_id",
        contract_price: "contract_unit_price",
    }

    if contract_id:
        rename_contract[
            contract_id
        ] = "contract_id"

    contract_data = contract_data.rename(
        columns=rename_contract
    )

    contract_data[
        "contract_unit_price"
    ] = numeric_series(
        contract_data[
            "contract_unit_price"
        ]
    )

    contract_data = (
        contract_data
        .dropna(
            subset=[
                "vendor_id",
                "contract_unit_price",
            ]
        )
        .drop_duplicates(
            subset=[
                "vendor_id"
            ]
        )
    )

    # --------------------------------------------------------
    # BUILD CLEAN INVOICE TABLE
    # --------------------------------------------------------

    invoice_columns = [
        invoice_vendor,
        invoice_id,
        invoice_price,
    ]

    if invoice_quantity:
        invoice_columns.append(
            invoice_quantity
        )

    invoice_data = invoices[
        invoice_columns
    ].copy()

    rename_invoice = {
        invoice_vendor: "vendor_id",
        invoice_id: "invoice_id",
        invoice_price: "invoice_unit_price",
    }

    if invoice_quantity:
        rename_invoice[
            invoice_quantity
        ] = "invoice_quantity"

    invoice_data = invoice_data.rename(
        columns=rename_invoice
    )

    invoice_data[
        "invoice_unit_price"
    ] = numeric_series(
        invoice_data[
            "invoice_unit_price"
        ]
    )

    if "invoice_quantity" in invoice_data.columns:

        invoice_data[
            "invoice_quantity"
        ] = numeric_series(
            invoice_data[
                "invoice_quantity"
            ]
        )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    merged = invoice_data.merge(
        contract_data,
        on="vendor_id",
        how="inner"
    )

    if merged.empty:

        print(
            "  No invoice/contract vendor matches found."
        )

        return results

    # --------------------------------------------------------
    # PRICE VARIANCE
    # --------------------------------------------------------

    merged[
        "price_difference"
    ] = (
        merged["invoice_unit_price"]
        - merged["contract_unit_price"]
    )

    merged[
        "price_difference_pct"
    ] = (
        merged["price_difference"]
        / merged[
            "contract_unit_price"
        ].replace(
            0,
            pd.NA
        )
    ) * 100

    violations = merged[
        merged["price_difference"] > 0
    ].copy()

    # --------------------------------------------------------
    # CREATE CLAIMS
    # --------------------------------------------------------

    for _, row in violations.iterrows():

        difference = to_numeric(
            row["price_difference"]
        )

        if difference is None:
            continue

        quantity = 1.0

        if "invoice_quantity" in row.index:

            quantity_value = to_numeric(
                row["invoice_quantity"]
            )

            if (
                quantity_value is not None
                and quantity_value > 0
            ):
                quantity = quantity_value

        leakage = max(
            0.0,
            difference * quantity
        )

        if leakage <= 0:
            continue

        contract_identifier = None

        if "contract_id" in row.index:

            contract_identifier = (
                row["contract_id"]
            )

        results.append(
            {
                "claim_id":
                    (
                        "CLM-CONTRACT-PRICE-"
                        f"{row['invoice_id']}"
                    ),

                "compliance_type":
                    "CONTRACT_PRICE_VIOLATION",

                "invoice_id":
                    row["invoice_id"],

                "vendor_id":
                    row["vendor_id"],

                "contract_id":
                    contract_identifier,

                "contract_value":
                    row[
                        "contract_unit_price"
                    ],

                "actual_value":
                    row[
                        "invoice_unit_price"
                    ],

                "variance":
                    difference,

                "variance_percentage":
                    to_numeric(
                        row[
                            "price_difference_pct"
                        ]
                    ),

                "potential_leakage":
                    leakage,

                "risk_level":
                    risk_level(
                        leakage
                    ),

                "confidence_score":
                    95.0,

                "currency":
                    "INR",

                "evidence":
                    (
                        "Invoice unit price "
                        f"{row['invoice_unit_price']:.2f} "
                        "is higher than contract unit "
                        "price "
                        f"{row['contract_unit_price']:.2f}."
                    ),

                "status":
                    "NEW",

                "detected_at":
                    datetime.utcnow().isoformat(),

                "engine_version":
                    "1.1.0",
            }
        )

    return results


# ============================================================
# CONTRACT REBATE COMPLIANCE
# ============================================================

def detect_rebate_violations(
    contracts: pd.DataFrame,
    rebates: pd.DataFrame
) -> list[dict]:
    """
    Compare expected contract rebates against
    actual credited rebates.
    """

    results = []

    if contracts.empty:
        return results

    if rebates.empty:
        return results

    # --------------------------------------------------------
    # CONTRACT COLUMNS
    # --------------------------------------------------------

    contract_vendor = first_existing_column(
        contracts,
        [
            "vendor_id",
            "vendor",
        ]
    )

    contract_rebate = first_existing_column(
        contracts,
        [
            "rebate_percentage",
        ]
    )

    contract_id = first_existing_column(
        contracts,
        [
            "contract_id",
        ]
    )

    if not contract_vendor:
        return results

    if not contract_rebate:
        print(
            "  Contract rebate column not found."
        )
        return results

    # --------------------------------------------------------
    # REBATE COLUMNS
    # --------------------------------------------------------

    rebate_vendor = first_existing_column(
        rebates,
        [
            "vendor_id",
            "vendor",
        ]
    )

    rebate_id = first_existing_column(
        rebates,
        [
            "rebate_id",
        ]
    )

    actual_rebate = first_existing_column(
        rebates,
        [
            "rebate_amount",
            "credited_amount",
            "credit_amount",
            "actual_rebate",
            "amount",
        ]
    )

    expected_rebate = first_existing_column(
        rebates,
        [
            "expected_rebate",
            "expected_rebate_amount",
        ]
    )

    base_amount = first_existing_column(
        rebates,
        [
            "eligible_amount",
            "purchase_amount",
            "invoice_amount",
            "sales_amount",
            "base_amount",
        ]
    )

    if not rebate_vendor:
        return results

    if not actual_rebate:
        print(
            "  Actual rebate column not found."
        )
        return results

    # --------------------------------------------------------
    # CLEAN CONTRACT DATA
    # --------------------------------------------------------

    contract_columns = [
        contract_vendor,
        contract_rebate,
    ]

    if contract_id:
        contract_columns.append(
            contract_id
        )

    contract_data = contracts[
        contract_columns
    ].copy()

    rename_contract = {
        contract_vendor: "vendor_id",
        contract_rebate: "contract_rebate_percentage",
    }

    if contract_id:
        rename_contract[
            contract_id
        ] = "contract_id"

    contract_data = contract_data.rename(
        columns=rename_contract
    )

    contract_data[
        "contract_rebate_percentage"
    ] = numeric_series(
        contract_data[
            "contract_rebate_percentage"
        ]
    )

    contract_data = (
        contract_data
        .dropna(
            subset=[
                "vendor_id",
                "contract_rebate_percentage",
            ]
        )
        .drop_duplicates(
            subset=[
                "vendor_id"
            ]
        )
    )

    # --------------------------------------------------------
    # CLEAN REBATE DATA
    # --------------------------------------------------------

    rebate_columns = [
        rebate_vendor,
        actual_rebate,
    ]

    if rebate_id:
        rebate_columns.append(
            rebate_id
        )

    if expected_rebate:
        rebate_columns.append(
            expected_rebate
        )

    if base_amount:
        rebate_columns.append(
            base_amount
        )

    rebate_data = rebates[
        rebate_columns
    ].copy()

    rename_rebate = {
        rebate_vendor: "vendor_id",
        actual_rebate: "actual_rebate",
    }

    if rebate_id:
        rename_rebate[
            rebate_id
        ] = "rebate_id"

    if expected_rebate:
        rename_rebate[
            expected_rebate
        ] = "expected_rebate"

    if base_amount:
        rename_rebate[
            base_amount
        ] = "base_amount"

    rebate_data = rebate_data.rename(
        columns=rename_rebate
    )

    rebate_data[
        "actual_rebate"
    ] = numeric_series(
        rebate_data[
            "actual_rebate"
        ]
    )

    if "expected_rebate" in rebate_data.columns:

        rebate_data[
            "expected_rebate"
        ] = numeric_series(
            rebate_data[
                "expected_rebate"
            ]
        )

    if "base_amount" in rebate_data.columns:

        rebate_data[
            "base_amount"
        ] = numeric_series(
            rebate_data[
                "base_amount"
            ]
        )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    merged = rebate_data.merge(
        contract_data,
        on="vendor_id",
        how="inner"
    )

    if merged.empty:

        print(
            "  No rebate/contract vendor matches found."
        )

        return results

    # --------------------------------------------------------
    # EXPECTED REBATE
    # --------------------------------------------------------

    if "expected_rebate" not in merged.columns:

        if "base_amount" not in merged.columns:

            print(
                "  Cannot calculate expected rebate "
                "because no rebate base amount exists."
            )

            return results

        merged[
            "expected_rebate"
        ] = (
            merged["base_amount"]
            * merged[
                "contract_rebate_percentage"
            ]
            / 100
        )

    merged[
        "missing_rebate"
    ] = (
        merged["expected_rebate"]
        - merged["actual_rebate"]
    )

    violations = merged[
        merged["missing_rebate"] > 0
    ].copy()

    # --------------------------------------------------------
    # CREATE CLAIMS
    # --------------------------------------------------------

    for index, row in violations.iterrows():

        leakage = to_numeric(
            row["missing_rebate"]
        )

        if leakage is None or leakage <= 0:
            continue

        rebate_identifier = (
            row["rebate_id"]
            if "rebate_id" in row.index
            else f"ROW-{index}"
        )

        contract_identifier = None

        if "contract_id" in row.index:
            contract_identifier = (
                row["contract_id"]
            )

        results.append(
            {
                "claim_id":
                    (
                        "CLM-CONTRACT-REBATE-"
                        f"{rebate_identifier}"
                    ),

                "compliance_type":
                    "CONTRACT_REBATE_VIOLATION",

                "invoice_id":
                    None,

                "vendor_id":
                    row["vendor_id"],

                "contract_id":
                    contract_identifier,

                "contract_value":
                    row[
                        "contract_rebate_percentage"
                    ],

                "actual_value":
                    row[
                        "actual_rebate"
                    ],

                "variance":
                    leakage,

                "variance_percentage":
                    None,

                "potential_leakage":
                    leakage,

                "risk_level":
                    risk_level(
                        leakage
                    ),

                "confidence_score":
                    92.0,

                "currency":
                    "INR",

                "evidence":
                    (
                        "Contract rebate: "
                        f"{row['contract_rebate_percentage']:.2f}%. "
                        "Expected rebate: "
                        f"₹{row['expected_rebate']:,.2f}. "
                        "Actual rebate: "
                        f"₹{row['actual_rebate']:,.2f}."
                    ),

                "status":
                    "NEW",

                "detected_at":
                    datetime.utcnow().isoformat(),

                "engine_version":
                    "1.1.0",
            }
        )

    return results


# ============================================================
# PAYMENT TERM COMPLIANCE
# ============================================================

def detect_payment_term_violations(
    contracts: pd.DataFrame,
    invoices: pd.DataFrame,
    payments: pd.DataFrame
) -> list[dict]:
    """
    Detect payments made earlier than contractual
    payment terms.

    This is treated as a REVIEW finding because
    early payment does not automatically represent
    confirmed financial leakage.
    """

    results = []

    if contracts.empty:
        return results

    if invoices.empty:
        return results

    if payments.empty:
        return results

    # --------------------------------------------------------
    # CONTRACT COLUMNS
    # --------------------------------------------------------

    contract_vendor = first_existing_column(
        contracts,
        [
            "vendor_id",
            "vendor",
        ]
    )

    payment_terms = first_existing_column(
        contracts,
        [
            "payment_terms",
        ]
    )

    contract_id = first_existing_column(
        contracts,
        [
            "contract_id",
        ]
    )

    if not contract_vendor:
        return results

    if not payment_terms:
        print(
            "  Contract payment terms column not found."
        )
        return results

    # --------------------------------------------------------
    # INVOICE COLUMNS
    # --------------------------------------------------------

    invoice_id = first_existing_column(
        invoices,
        [
            "invoice_id",
        ]
    )

    invoice_vendor = first_existing_column(
        invoices,
        [
            "vendor_id",
            "vendor",
        ]
    )

    invoice_date = first_existing_column(
        invoices,
        [
            "invoice_date",
        ]
    )

    if not invoice_id:
        return results

    if not invoice_vendor:
        return results

    if not invoice_date:
        return results

    # --------------------------------------------------------
    # PAYMENT COLUMNS
    # --------------------------------------------------------

    payment_invoice = first_existing_column(
        payments,
        [
            "invoice_id",
        ]
    )

    payment_date = first_existing_column(
        payments,
        [
            "payment_date",
        ]
    )

    if not payment_invoice:
        return results

    if not payment_date:
        return results

    # --------------------------------------------------------
    # CLEAN CONTRACT DATA
    # --------------------------------------------------------

    contract_columns = [
        contract_vendor,
        payment_terms,
    ]

    if contract_id:
        contract_columns.append(
            contract_id
        )

    contract_data = contracts[
        contract_columns
    ].copy()

    rename_contract = {
        contract_vendor: "vendor_id",
        payment_terms: "contract_payment_terms",
    }

    if contract_id:
        rename_contract[
            contract_id
        ] = "contract_id"

    contract_data = contract_data.rename(
        columns=rename_contract
    )

    contract_data = (
        contract_data
        .dropna(
            subset=[
                "vendor_id",
                "contract_payment_terms",
            ]
        )
        .drop_duplicates(
            subset=[
                "vendor_id"
            ]
        )
    )

    # --------------------------------------------------------
    # CLEAN INVOICE DATA
    # --------------------------------------------------------

    invoice_data = invoices[
        [
            invoice_id,
            invoice_vendor,
            invoice_date,
        ]
    ].copy()

    invoice_data = invoice_data.rename(
        columns={
            invoice_id: "invoice_id",
            invoice_vendor: "vendor_id",
            invoice_date: "invoice_date",
        }
    )

    # --------------------------------------------------------
    # CLEAN PAYMENT DATA
    # --------------------------------------------------------

    payment_data = payments[
        [
            payment_invoice,
            payment_date,
        ]
    ].copy()

    payment_data = payment_data.rename(
        columns={
            payment_invoice: "invoice_id",
            payment_date: "payment_date",
        }
    )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    merged = payment_data.merge(
        invoice_data,
        on="invoice_id",
        how="inner"
    )

    merged = merged.merge(
        contract_data,
        on="vendor_id",
        how="inner"
    )

    if merged.empty:

        print(
            "  No payment/contract matches found."
        )

        return results

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    merged[
        "invoice_date"
    ] = pd.to_datetime(
        merged["invoice_date"],
        errors="coerce"
    )

    merged[
        "payment_date"
    ] = pd.to_datetime(
        merged["payment_date"],
        errors="coerce"
    )

    merged[
        "days_to_payment"
    ] = (
        merged["payment_date"]
        - merged["invoice_date"]
    ).dt.days

    # --------------------------------------------------------
    # EXTRACT NET DAYS
    # --------------------------------------------------------

    merged[
        "allowed_days"
    ] = (
        merged[
            "contract_payment_terms"
        ]
        .astype(str)
        .str.extract(
            r"(\d+)"
        )[0]
    )

    merged[
        "allowed_days"
    ] = pd.to_numeric(
        merged["allowed_days"],
        errors="coerce"
    )

    violations = merged[
        (
            merged["days_to_payment"]
            < merged["allowed_days"]
        )
        &
        merged["days_to_payment"].notna()
        &
        merged["allowed_days"].notna()
    ].copy()

    # --------------------------------------------------------
    # CREATE REVIEW FINDINGS
    # --------------------------------------------------------

    for _, row in violations.iterrows():

        early_days = (
            row["allowed_days"]
            - row["days_to_payment"]
        )

        if early_days <= 0:
            continue

        contract_identifier = None

        if "contract_id" in row.index:

            contract_identifier = (
                row["contract_id"]
            )

        results.append(
            {
                "claim_id":
                    (
                        "CLM-CONTRACT-PAYMENT-"
                        f"{row['invoice_id']}"
                    ),

                "compliance_type":
                    "EARLY_PAYMENT_REVIEW",

                "invoice_id":
                    row["invoice_id"],

                "vendor_id":
                    row["vendor_id"],

                "contract_id":
                    contract_identifier,

                "contract_value":
                    row[
                        "contract_payment_terms"
                    ],

                "actual_value":
                    (
                        f"{int(row['days_to_payment'])} "
                        "days"
                    ),

                "variance":
                    float(early_days),

                "variance_percentage":
                    None,

                "potential_leakage":
                    0.0,

                "risk_level":
                    "LOW",

                "confidence_score":
                    90.0,

                "currency":
                    "INR",

                "evidence":
                    (
                        "Contract payment terms: "
                        f"{row['contract_payment_terms']}. "
                        "Payment was made after "
                        f"{int(row['days_to_payment'])} days, "
                        "which is earlier than the contractual "
                        f"{int(row['allowed_days'])}-day term."
                    ),

                "status":
                    "REVIEW",

                "detected_at":
                    datetime.utcnow().isoformat(),

                "engine_version":
                    "1.1.0",
            }
        )

    return results


# ============================================================
# MAIN ENGINE
# ============================================================

def run_contract_compliance():

    print()
    print("=" * 70)
    print(
        "DOLLARGUARD AI - "
        "CONTRACT COMPLIANCE ENGINE"
    )
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    contracts = load_contracts()

    invoices = load_csv(
        "invoices.csv"
    )

    rebates = load_csv(
        "rebates.csv"
    )

    payments = load_csv(
        "payments.csv"
    )

    print(
        f"Contracts loaded : {len(contracts):,}"
    )

    print(
        f"Invoices loaded  : {len(invoices):,}"
    )

    print(
        f"Rebates loaded   : {len(rebates):,}"
    )

    print(
        f"Payments loaded  : {len(payments):,}"
    )

    print()

    all_results = []

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    print(
        "Running contract price compliance..."
    )

    price_results = detect_price_violations(
        contracts,
        invoices
    )

    print(
        f"  Claims detected: "
        f"{len(price_results):,}"
    )

    all_results.extend(
        price_results
    )

    # --------------------------------------------------------
    # REBATE
    # --------------------------------------------------------

    print(
        "Running contract rebate compliance..."
    )

    rebate_results = detect_rebate_violations(
        contracts,
        rebates
    )

    print(
        f"  Claims detected: "
        f"{len(rebate_results):,}"
    )

    all_results.extend(
        rebate_results
    )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    print(
        "Running payment-term compliance..."
    )

    payment_results = (
        detect_payment_term_violations(
            contracts,
            invoices,
            payments
        )
    )

    print(
        f"  Review findings: "
        f"{len(payment_results):,}"
    )

    all_results.extend(
        payment_results
    )

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    dataframe = pd.DataFrame(
        all_results
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "claim_id",
        "compliance_type",
        "invoice_id",
        "vendor_id",
        "contract_id",
        "contract_value",
        "actual_value",
        "variance",
        "variance_percentage",
        "potential_leakage",
        "risk_level",
        "confidence_score",
        "currency",
        "evidence",
        "status",
        "detected_at",
        "engine_version",
    ]

    if dataframe.empty:

        dataframe = pd.DataFrame(
            columns=columns
        )

    else:

        for column in columns:

            if column not in dataframe.columns:

                dataframe[column] = None

        dataframe = dataframe[
            columns
        ]

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print(
        "CONTRACT COMPLIANCE COMPLETE"
    )
    print("=" * 70)
    print()

    print(
        f"Compliance findings : "
        f"{len(dataframe):,}"
    )

    if not dataframe.empty:

        leakage = numeric_series(
            dataframe[
                "potential_leakage"
            ]
        ).fillna(0)

        total_leakage = leakage.sum()

        print(
            f"Potential leakage   : "
            f"₹{total_leakage:,.2f}"
        )

        print()

        print(
            "Compliance Types:"
        )

        type_counts = (
            dataframe[
                "compliance_type"
            ]
            .value_counts()
        )

        for name, count in type_counts.items():

            print(
                f"  {name:<35}"
                f"{count:,}"
            )

        print()

        print(
            "Risk Distribution:"
        )

        risk_counts = (
            dataframe[
                "risk_level"
            ]
            .value_counts()
        )

        for risk in [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
        ]:

            print(
                f"  {risk:<10}: "
                f"{risk_counts.get(risk, 0):,}"
            )

        print()

        print(
            "Top 10 Findings:"
        )

        display_columns = [
            "claim_id",
            "compliance_type",
            "vendor_id",
            "invoice_id",
            "potential_leakage",
            "risk_level",
        ]

        available_columns = [
            column
            for column in display_columns
            if column in dataframe.columns
        ]

        print(
            dataframe[
                available_columns
            ]
            .sort_values(
                "potential_leakage",
                ascending=False
            )
            .head(10)
            .to_string(
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

    return dataframe


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_contract_compliance()