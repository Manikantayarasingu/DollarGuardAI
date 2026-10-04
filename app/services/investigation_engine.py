from pathlib import Path
from datetime import datetime
import json

import pandas as pd


# ============================================================
# DOLLARGUARD AI - INVESTIGATION EVIDENCE ENGINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"

INVESTIGATIONS_FILE = PROCESSED_DIR / "investigation_reports.csv"
UNIFIED_CLAIMS_FILE = PROCESSED_DIR / "unified_claims.csv"

CONTRACTS_FILE = SYNTHETIC_DIR / "contracts.csv"
PURCHASE_ORDERS_FILE = SYNTHETIC_DIR / "purchase_orders.csv"
INVOICES_FILE = SYNTHETIC_DIR / "invoices.csv"
PAYMENTS_FILE = SYNTHETIC_DIR / "payments.csv"
REBATES_FILE = SYNTHETIC_DIR / "rebates.csv"

OUTPUT_FILE = PROCESSED_DIR / "investigation_packets.csv"


# ============================================================
# HELPERS
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV safely."""

    if not path.exists():
        print(f"WARNING: File not found: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as exc:
        print(f"WARNING: Could not read {path.name}: {exc}")
        return pd.DataFrame()


def find_column(df: pd.DataFrame, candidates):
    """Find the first matching column from a list of candidates."""

    if df.empty:
        return None

    normalized = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().lower()

        if key in normalized:
            return normalized[key]

    return None


def get_value(row, candidates, default=None):
    """Get a value from a row using possible column names."""

    if row is None:
        return default

    for candidate in candidates:
        if candidate in row.index:
            value = row[candidate]

            if pd.notna(value):
                return value

    return default


def safe_float(value, default=0.0):
    """Convert a value to float safely."""

    try:
        if pd.isna(value):
            return default

        return float(value)

    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Convert a value to integer safely."""

    try:
        if pd.isna(value):
            return default

        return int(float(value))

    except (ValueError, TypeError):
        return default


def build_lookup(df: pd.DataFrame, key_candidates):
    """Create a dictionary lookup using the first available ID column."""

    if df.empty:
        return {}

    key_column = find_column(df, key_candidates)

    if key_column is None:
        return {}

    lookup = {}

    for _, row in df.iterrows():
        key = row.get(key_column)

        if pd.isna(key):
            continue

        lookup[str(key).strip()] = row

    return lookup


def build_group_lookup(df: pd.DataFrame, key_candidates):
    """Create a lookup where one key can have multiple records."""

    if df.empty:
        return {}

    key_column = find_column(df, key_candidates)

    if key_column is None:
        return {}

    result = {}

    for _, row in df.iterrows():
        key = row.get(key_column)

        if pd.isna(key):
            continue

        key = str(key).strip()

        if key not in result:
            result[key] = []

        result[key].append(row)

    return result


def json_safe(value):
    """Convert values into JSON-safe Python values."""

    if pd.isna(value):
        return None

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()

    try:
        return value.item()
    except Exception:
        return value


# ============================================================
# EVIDENCE CALCULATION
# ============================================================

def calculate_evidence_coverage(
    claim,
    contract,
    purchase_order,
    invoice,
    payments,
    rebate_rows,
):
    """
    Calculate how much supporting evidence is available.

    This is an evidence coverage metric, not a probability
    that fraud or intentional wrongdoing occurred.
    """

    available = 0
    total = 6

    if claim is not None:
        available += 1

    if contract is not None:
        available += 1

    if purchase_order is not None:
        available += 1

    if invoice is not None:
        available += 1

    if payments:
        available += 1

    if rebate_rows:
        available += 1

    coverage = round((available / total) * 100, 2)

    return coverage


# ============================================================
# DISCREPANCY CALCULATIONS
# ============================================================

def calculate_discrepancies(
    contract,
    purchase_order,
    invoice,
    payments,
    rebate_rows,
):
    """Calculate transaction-level discrepancies."""

    contract_price = safe_float(
        get_value(
            contract,
            [
                "unit_price",
                "contract_unit_price",
                "price",
            ],
        )
    )

    po_price = safe_float(
        get_value(
            purchase_order,
            [
                "unit_price",
                "po_unit_price",
                "price",
            ],
        )
    )

    invoice_price = safe_float(
        get_value(
            invoice,
            [
                "unit_price",
                "invoice_unit_price",
                "price",
            ],
        )
    )

    po_quantity = safe_float(
        get_value(
            purchase_order,
            [
                "quantity",
                "po_quantity",
                "ordered_quantity",
            ],
        )
    )

    invoice_quantity = safe_float(
        get_value(
            invoice,
            [
                "quantity",
                "invoice_quantity",
                "billed_quantity",
            ],
        )
    )

    invoice_amount = safe_float(
        get_value(
            invoice,
            [
                "invoice_amount",
                "amount",
                "total_amount",
            ]
        )
    )

    total_paid = 0.0

    for payment in payments:
        total_paid += safe_float(
            get_value(
                payment,
                [
                    "payment_amount",
                    "amount",
                    "paid_amount",
                ],
            )
        )

    payment_overage = max(total_paid - invoice_amount, 0.0)

    price_variance = 0.0

    if contract_price > 0 and invoice_price > contract_price:
        price_variance = invoice_price - contract_price

    quantity_variance = max(
        invoice_quantity - po_quantity,
        0.0
    )

    rebate_percentage = 0.0

    if contract is not None:
        rebate_percentage = safe_float(
            get_value(
                contract,
                [
                    "rebate_percentage",
                    "rebate_percent",
                ],
            )
        )

    expected_rebate = 0.0

    if invoice_amount > 0 and rebate_percentage > 0:
        expected_rebate = (
            invoice_amount * rebate_percentage / 100
        )

    credited_rebate = 0.0

    for rebate in rebate_rows:
        credited_rebate += safe_float(
            get_value(
                rebate,
                [
                    "rebate_amount",
                    "credited_amount",
                    "credit_amount",
                    "amount",
                ],
            )
        )

    missing_rebate = max(
        expected_rebate - credited_rebate,
        0.0,
    )

    return {
        "contract_unit_price": round(contract_price, 2),
        "po_unit_price": round(po_price, 2),
        "invoice_unit_price": round(invoice_price, 2),
        "po_quantity": round(po_quantity, 2),
        "invoice_quantity": round(invoice_quantity, 2),
        "invoice_amount": round(invoice_amount, 2),
        "total_paid": round(total_paid, 2),
        "payment_overage": round(payment_overage, 2),
        "price_variance": round(price_variance, 2),
        "quantity_variance": round(quantity_variance, 2),
        "contract_rebate_percentage": round(
            rebate_percentage,
            2,
        ),
        "expected_rebate": round(
            expected_rebate,
            2,
        ),
        "credited_rebate": round(
            credited_rebate,
            2,
        ),
        "missing_rebate": round(
            missing_rebate,
            2,
        ),
    }


# ============================================================
# EVIDENCE CHAIN
# ============================================================

def build_evidence_chain(
    claim,
    contract,
    purchase_order,
    invoice,
    payments,
    rebate_rows,
):
    """Create a structured evidence chain."""

    chain = []

    if contract is not None:
        contract_id = get_value(
            contract,
            ["contract_id", "id"],
            "UNKNOWN",
        )

        chain.append(
            {
                "stage": "CONTRACT",
                "status": "AVAILABLE",
                "reference": str(contract_id),
                "description": (
                    "Contract terms available for comparison."
                ),
            }
        )
    else:
        chain.append(
            {
                "stage": "CONTRACT",
                "status": "MISSING",
                "reference": None,
                "description": (
                    "No matching contract record found."
                ),
            }
        )

    if purchase_order is not None:
        po_id = get_value(
            purchase_order,
            ["po_id", "purchase_order_id", "id"],
            "UNKNOWN",
        )

        chain.append(
            {
                "stage": "PURCHASE_ORDER",
                "status": "AVAILABLE",
                "reference": str(po_id),
                "description": (
                    "Purchase order available for "
                    "quantity and price validation."
                ),
            }
        )
    else:
        chain.append(
            {
                "stage": "PURCHASE_ORDER",
                "status": "MISSING",
                "reference": None,
                "description": (
                    "No matching purchase order found."
                ),
            }
        )

    if invoice is not None:
        invoice_id = get_value(
            invoice,
            ["invoice_id", "id"],
            "UNKNOWN",
        )

        chain.append(
            {
                "stage": "INVOICE",
                "status": "AVAILABLE",
                "reference": str(invoice_id),
                "description": (
                    "Invoice available for transaction "
                    "validation."
                ),
            }
        )
    else:
        chain.append(
            {
                "stage": "INVOICE",
                "status": "MISSING",
                "reference": None,
                "description": (
                    "No matching invoice found."
                ),
            }
        )

    if payments:
        payment_ids = []

        for payment in payments:
            payment_id = get_value(
                payment,
                [
                    "payment_id",
                    "id",
                ],
                "UNKNOWN",
            )

            payment_ids.append(str(payment_id))

        chain.append(
            {
                "stage": "PAYMENT",
                "status": "AVAILABLE",
                "reference": ", ".join(payment_ids[:10]),
                "description": (
                    f"{len(payments)} payment record(s) "
                    "linked to the invoice."
                ),
            }
        )
    else:
        chain.append(
            {
                "stage": "PAYMENT",
                "status": "MISSING",
                "reference": None,
                "description": (
                    "No payment records found."
                ),
            }
        )

    if rebate_rows:
        rebate_ids = []

        for rebate in rebate_rows:
            rebate_id = get_value(
                rebate,
                [
                    "rebate_id",
                    "id",
                ],
                "UNKNOWN",
            )

            rebate_ids.append(str(rebate_id))

        chain.append(
            {
                "stage": "REBATE",
                "status": "AVAILABLE",
                "reference": ", ".join(rebate_ids[:10]),
                "description": (
                    f"{len(rebate_rows)} rebate record(s) "
                    "available for validation."
                ),
            }
        )

    return chain


# ============================================================
# INVESTIGATION CONCLUSION
# ============================================================

def generate_conclusion(
    leakage_type,
    discrepancies,
    evidence_coverage,
):
    """Generate a deterministic investigation conclusion."""

    findings = []

    if discrepancies["price_variance"] > 0:
        findings.append(
            "Invoice unit price exceeds the available "
            "contract unit price."
        )

    if discrepancies["quantity_variance"] > 0:
        findings.append(
            "Invoice quantity exceeds the available "
            "purchase-order quantity."
        )

    if discrepancies["payment_overage"] > 0:
        findings.append(
            "Recorded payments exceed the invoice amount."
        )

    if discrepancies["missing_rebate"] > 0:
        findings.append(
            "Expected contractual rebate exceeds the "
            "recorded rebate credit."
        )

    if not findings:
        findings.append(
            "No additional transaction discrepancy was "
            "calculated from the linked records."
        )

    conclusion = " ".join(findings)

    return (
        f"Leakage category: {leakage_type}. "
        f"Evidence coverage: {evidence_coverage}%. "
        f"{conclusion}"
    )


def generate_recovery_action(
    leakage_type,
    discrepancies,
):
    """Generate a recovery action based on the evidence."""

    actions = []

    if discrepancies["price_variance"] > 0:
        actions.append(
            "Request supplier credit for the contract-price variance."
        )

    if discrepancies["quantity_variance"] > 0:
        actions.append(
            "Validate receiving records and request adjustment "
            "for excess billed quantity."
        )

    if discrepancies["payment_overage"] > 0:
        actions.append(
            "Initiate payment reconciliation and recovery "
            "for the payment overage."
        )

    if discrepancies["missing_rebate"] > 0:
        actions.append(
            "Request the missing contractual rebate or credit note."
        )

    if not actions:
        actions.append(
            "Route the case to manual investigation "
            "before recovery action."
        )

    return " ".join(actions)


# ============================================================
# PACKET BUILDER
# ============================================================

def build_investigation_packets():
    print("=" * 70)
    print("DOLLARGUARD AI - INVESTIGATION EVIDENCE ENGINE")
    print("=" * 70)

    investigations = load_csv(INVESTIGATIONS_FILE)
    unified_claims = load_csv(UNIFIED_CLAIMS_FILE)

    contracts = load_csv(CONTRACTS_FILE)
    purchase_orders = load_csv(PURCHASE_ORDERS_FILE)
    invoices = load_csv(INVOICES_FILE)
    payments = load_csv(PAYMENTS_FILE)
    rebates = load_csv(REBATES_FILE)

    print()
    print("Source datasets:")
    print(f"  Investigations : {len(investigations):,}")
    print(f"  Unified claims : {len(unified_claims):,}")
    print(f"  Contracts      : {len(contracts):,}")
    print(f"  Purchase orders: {len(purchase_orders):,}")
    print(f"  Invoices       : {len(invoices):,}")
    print(f"  Payments       : {len(payments):,}")
    print(f"  Rebates        : {len(rebates):,}")

    if investigations.empty:
        print()
        print("ERROR: investigation_reports.csv is empty or missing.")
        return

    # --------------------------------------------------------
    # LOOKUPS
    # --------------------------------------------------------

    claim_lookup = build_lookup(
        unified_claims,
        [
            "claim_id",
            "original_claim_id",
        ],
    )

    contract_lookup = build_lookup(
        contracts,
        [
            "contract_id",
            "id",
        ],
    )

    po_lookup = build_lookup(
        purchase_orders,
        [
            "po_id",
            "purchase_order_id",
            "id",
        ],
    )

    invoice_lookup = build_lookup(
        invoices,
        [
            "invoice_id",
            "id",
        ],
    )

    payment_lookup = build_group_lookup(
        payments,
        [
            "invoice_id",
        ],
    )

    rebate_lookup = build_group_lookup(
        rebates,
        [
            "rebate_id",
            "invoice_id",
            "vendor_id",
        ],
    )

    # --------------------------------------------------------
    # INVESTIGATION COLUMN DETECTION
    # --------------------------------------------------------

    investigation_id_col = find_column(
        investigations,
        [
            "investigation_id",
            "id",
        ],
    )

    claim_id_col = find_column(
        investigations,
        [
            "claim_id",
            "original_claim_id",
            "recovery_claim_id",
        ],
    )

    if investigation_id_col is None:
        investigations["investigation_id"] = [
            f"INVEST-{i:07d}"
            for i in range(1, len(investigations) + 1)
        ]

        investigation_id_col = "investigation_id"

    # --------------------------------------------------------
    # BUILD PACKETS
    # --------------------------------------------------------

    packets = []

    for index, investigation in investigations.iterrows():

        investigation_id = get_value(
            investigation,
            [investigation_id_col],
            f"INVEST-{index + 1:07d}",
        )

        claim_id = get_value(
            investigation,
            [
                claim_id_col,
                "claim_id",
                "original_claim_id",
            ],
            None,
        )

        if claim_id is not None:
            claim_id = str(claim_id).strip()

        claim = claim_lookup.get(claim_id)

        vendor_id = get_value(
            investigation,
            ["vendor_id"],
            None,
        )

        invoice_id = get_value(
            investigation,
            ["invoice_id"],
            None,
        )

        po_id = get_value(
            investigation,
            ["po_id"],
            None,
        )

        contract_id = get_value(
            investigation,
            ["contract_id"],
            None,
        )

        # Fall back to claim values when investigation
        # doesn't contain the relationship.
        if claim is not None:

            if vendor_id is None:
                vendor_id = get_value(
                    claim,
                    ["vendor_id"],
                    None,
                )

            if invoice_id is None:
                invoice_id = get_value(
                    claim,
                    ["invoice_id"],
                    None,
                )

            if po_id is None:
                po_id = get_value(
                    claim,
                    ["po_id"],
                    None,
                )

            if contract_id is None:
                contract_id = get_value(
                    claim,
                    ["contract_id"],
                    None,
                )

        vendor_id = (
            str(vendor_id).strip()
            if vendor_id is not None
            else None
        )

        invoice_id = (
            str(invoice_id).strip()
            if invoice_id is not None
            else None
        )

        po_id = (
            str(po_id).strip()
            if po_id is not None
            else None
        )

        contract_id = (
            str(contract_id).strip()
            if contract_id is not None
            else None
        )

        # ----------------------------------------------------
        # Resolve records
        # ----------------------------------------------------

        contract = (
            contract_lookup.get(contract_id)
            if contract_id
            else None
        )

        purchase_order = (
            po_lookup.get(po_id)
            if po_id
            else None
        )

        invoice = (
            invoice_lookup.get(invoice_id)
            if invoice_id
            else None
        )

        linked_payments = (
            payment_lookup.get(invoice_id, [])
            if invoice_id
            else []
        )

        linked_rebates = []

        if invoice_id:
            linked_rebates = rebate_lookup.get(
                invoice_id,
                [],
            )

        if not linked_rebates and vendor_id:
            linked_rebates = rebate_lookup.get(
                vendor_id,
                [],
            )

        # ----------------------------------------------------
        # Calculate discrepancies
        # ----------------------------------------------------

        discrepancies = calculate_discrepancies(
            contract=contract,
            purchase_order=purchase_order,
            invoice=invoice,
            payments=linked_payments,
            rebate_rows=linked_rebates,
        )

        evidence_coverage = calculate_evidence_coverage(
            claim=claim,
            contract=contract,
            purchase_order=purchase_order,
            invoice=invoice,
            payments=linked_payments,
            rebate_rows=linked_rebates,
        )

        leakage_type = get_value(
            investigation,
            [
                "leakage_type",
                "investigation_category",
                "category",
            ],
            get_value(
                claim,
                ["leakage_type"],
                "UNKNOWN",
            ),
        )

        risk_level = get_value(
            investigation,
            [
                "risk_level",
            ],
            get_value(
                claim,
                ["risk_level"],
                "UNKNOWN",
            ),
        )

        investigation_priority = get_value(
            investigation,
            [
                "investigation_priority",
                "priority",
            ],
            "P4",
        )

        potential_leakage = safe_float(
            get_value(
                investigation,
                [
                    "potential_leakage",
                ],
                get_value(
                    claim,
                    ["potential_leakage"],
                    0,
                ),
            )
        )

        evidence_chain = build_evidence_chain(
            claim=claim,
            contract=contract,
            purchase_order=purchase_order,
            invoice=invoice,
            payments=linked_payments,
            rebate_rows=linked_rebates,
        )

        conclusion = generate_conclusion(
            leakage_type=str(leakage_type),
            discrepancies=discrepancies,
            evidence_coverage=evidence_coverage,
        )

        recovery_action = generate_recovery_action(
            leakage_type=str(leakage_type),
            discrepancies=discrepancies,
        )

        packet = {
            "investigation_packet_id": (
                f"PACKET-{index + 1:07d}"
            ),
            "investigation_id": str(
                investigation_id
            ),
            "claim_id": claim_id,
            "vendor_id": vendor_id,
            "invoice_id": invoice_id,
            "po_id": po_id,
            "contract_id": contract_id,

            "leakage_type": leakage_type,
            "risk_level": risk_level,
            "investigation_priority": investigation_priority,

            "potential_leakage": round(
                potential_leakage,
                2,
            ),

            "contract_unit_price": discrepancies[
                "contract_unit_price"
            ],
            "po_unit_price": discrepancies[
                "po_unit_price"
            ],
            "invoice_unit_price": discrepancies[
                "invoice_unit_price"
            ],

            "po_quantity": discrepancies[
                "po_quantity"
            ],
            "invoice_quantity": discrepancies[
                "invoice_quantity"
            ],

            "invoice_amount": discrepancies[
                "invoice_amount"
            ],

            "total_paid": discrepancies[
                "total_paid"
            ],

            "payment_overage": discrepancies[
                "payment_overage"
            ],

            "price_variance": discrepancies[
                "price_variance"
            ],

            "quantity_variance": discrepancies[
                "quantity_variance"
            ],

            "contract_rebate_percentage": discrepancies[
                "contract_rebate_percentage"
            ],

            "expected_rebate": discrepancies[
                "expected_rebate"
            ],

            "credited_rebate": discrepancies[
                "credited_rebate"
            ],

            "missing_rebate": discrepancies[
                "missing_rebate"
            ],

            "evidence_coverage": evidence_coverage,

            "evidence_chain": json.dumps(
                evidence_chain,
                default=json_safe,
            ),

            "investigation_conclusion": conclusion,

            "recommended_recovery_action": (
                recovery_action
            ),

            "packet_status": "READY_FOR_REVIEW",

            "created_at": datetime.utcnow().isoformat(),
        }

        packets.append(packet)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output_df = pd.DataFrame(packets)

    if output_df.empty:
        print()
        print("ERROR: No investigation packets were created.")
        return

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_potential = output_df[
        "potential_leakage"
    ].sum()

    average_coverage = output_df[
        "evidence_coverage"
    ].mean()

    ready_count = (
        output_df["packet_status"]
        == "READY_FOR_REVIEW"
    ).sum()

    print()
    print("=" * 70)
    print("INVESTIGATION PACKET SUMMARY")
    print("=" * 70)

    print(
        f"Investigation packets : "
        f"{len(output_df):,}"
    )

    print(
        f"Potential exposure    : "
        f"₹{total_potential:,.2f}"
    )

    print(
        f"Average evidence      : "
        f"{average_coverage:.2f}%"
    )

    print(
        f"Ready for review      : "
        f"{ready_count:,}"
    )

    print()
    print("Leakage Categories:")

    category_counts = (
        output_df["leakage_type"]
        .value_counts()
    )

    for category, count in category_counts.items():
        print(
            f"  {str(category):25} : {count:,}"
        )

    print()
    print("Output file:")
    print(f"  {OUTPUT_FILE}")

    print()
    print("Sample investigation packet:")

    sample_columns = [
        "investigation_packet_id",
        "investigation_id",
        "claim_id",
        "vendor_id",
        "invoice_id",
        "po_id",
        "contract_id",
        "leakage_type",
        "potential_leakage",
        "evidence_coverage",
        "packet_status",
    ]

    print(
        output_df[
            sample_columns
        ].head(5).to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_investigation_packets()