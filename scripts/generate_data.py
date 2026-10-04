"""
DollarGuard AI
Enterprise Synthetic Financial Data Generator

Generates realistic synthetic enterprise procurement and
payment data for revenue leakage detection.

Data generated:
    - Vendors
    - Contracts
    - Purchase Orders
    - Goods Receipts
    - Invoices
    - Payments
    - Rebates
    - Credit Notes

Known leakage scenarios are intentionally injected so that
the detection engine can later be evaluated against ground truth.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "data" / "synthetic"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATASET SIZES
# ============================================================

NUM_VENDORS = 150
NUM_CONTRACTS = 500
NUM_PURCHASE_ORDERS = 5000
NUM_GOODS_RECEIPTS = 5000
NUM_INVOICES = 7500
NUM_PAYMENTS = 7500
NUM_REBATES = 750
NUM_CREDIT_NOTES = 500


# ============================================================
# MASTER DATA
# ============================================================

CATEGORIES = [
    "Raw Materials",
    "IT Equipment",
    "Office Supplies",
    "Logistics",
    "Packaging",
    "Maintenance",
    "Professional Services",
    "Marketing",
    "Facilities",
    "Safety Equipment",
]

REGIONS = [
    "India",
    "United States",
    "United Kingdom",
    "Germany",
    "Singapore",
    "Australia",
]

CITIES = [
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Mumbai",
    "Delhi",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Noida",
    "Gurugram",
]

PRODUCTS = [
    ("SKU-1001", "Industrial Bearings"),
    ("SKU-1002", "Steel Components"),
    ("SKU-1003", "Copper Wire"),
    ("SKU-1004", "Safety Gloves"),
    ("SKU-1005", "Packaging Boxes"),
    ("SKU-1006", "Laptop Computers"),
    ("SKU-1007", "Network Switches"),
    ("SKU-1008", "Office Chairs"),
    ("SKU-1009", "Printer Toner"),
    ("SKU-1010", "Cleaning Supplies"),
    ("SKU-1011", "LED Lighting"),
    ("SKU-1012", "Electrical Components"),
    ("SKU-1013", "Machine Oil"),
    ("SKU-1014", "Plastic Containers"),
    ("SKU-1015", "Industrial Tools"),
    ("SKU-1016", "Cloud Services"),
    ("SKU-1017", "Security Services"),
    ("SKU-1018", "Transport Services"),
    ("SKU-1019", "Marketing Services"),
    ("SKU-1020", "Maintenance Services"),
]


# ============================================================
# DATE HELPERS
# ============================================================

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 8, 31)


def random_date(
    start: date = START_DATE,
    end: date = END_DATE,
) -> date:
    """
    Generate a deterministic random date.
    """

    days = (end - start).days

    return start + timedelta(
        days=random.randint(0, days)
    )


def random_date_after(
    start: date,
    max_days: int = 90,
) -> date:
    """
    Generate a date after a supplied date.
    """

    return start + timedelta(
        days=random.randint(1, max_days)
    )


# ============================================================
# UTILITY HELPERS
# ============================================================

def money(value: float) -> float:
    """
    Round monetary values to two decimal places.
    """

    return round(float(value), 2)


def random_quantity(
    minimum: int = 10,
    maximum: int = 1000,
) -> int:
    return random.randint(
        minimum,
        maximum,
    )


def random_unit_price() -> float:
    """
    Generate realistic enterprise unit prices.
    """

    return money(
        random.uniform(50, 50000)
    )


# ============================================================
# 1. VENDORS
# ============================================================

def generate_vendors() -> pd.DataFrame:

    records = []

    for index in range(1, NUM_VENDORS + 1):

        vendor_id = f"VEN-{index:04d}"

        company_name = (
            fake.company()
            .replace(",", "")
        )

        category = random.choice(
            CATEGORIES
        )

        city = random.choice(
            CITIES
        )

        country = random.choice(
            REGIONS
        )

        annual_spend = money(
            random.uniform(
                500000,
                500000000,
            )
        )

        vendor_age = random.randint(
            1,
            25,
        )

        risk_score = money(
            random.uniform(
                5,
                75,
            )
        )

        records.append(
            {
                "vendor_id": vendor_id,
                "vendor_name": company_name,
                "category": category,
                "city": city,
                "country": country,
                "annual_spend": annual_spend,
                "vendor_age_years": vendor_age,
                "baseline_risk_score": risk_score,
                "active": True,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 2. CONTRACTS
# ============================================================

def generate_contracts(
    vendors: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index in range(1, NUM_CONTRACTS + 1):

        vendor = vendors.sample(
            1,
            random_state=SEED + index,
        ).iloc[0]

        sku, product_name = random.choice(
            PRODUCTS
        )

        contract_start = random_date()

        contract_end = contract_start + timedelta(
            days=random.choice(
                [180, 365, 540, 730]
            )
        )

        contract_price = random_unit_price()

        rebate_percentage = round(
            random.choice(
                [
                    0,
                    0,
                    0,
                    2,
                    3,
                    5,
                    7,
                    10,
                ]
            ),
            2,
        )

        payment_terms = random.choice(
            [
                "NET 15",
                "NET 30",
                "NET 45",
                "NET 60",
                "NET 90",
            ]
        )

        records.append(
            {
                "contract_id": f"CON-{index:05d}",
                "vendor_id": vendor["vendor_id"],
                "sku": sku,
                "product_name": product_name,
                "contract_price": contract_price,
                "rebate_percentage": rebate_percentage,
                "valid_from": contract_start,
                "valid_to": contract_end,
                "payment_terms": payment_terms,
                "status": "ACTIVE",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 3. PURCHASE ORDERS
# ============================================================

def generate_purchase_orders(
    vendors: pd.DataFrame,
    contracts: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index in range(1, NUM_PURCHASE_ORDERS + 1):

        vendor = vendors.sample(
            1,
            random_state=SEED + index + 1000,
        ).iloc[0]

        vendor_contracts = contracts[
            contracts["vendor_id"]
            == vendor["vendor_id"]
        ]

        if len(vendor_contracts) > 0:

            contract = vendor_contracts.sample(
                1,
                random_state=SEED + index + 2000,
            ).iloc[0]

            sku = contract["sku"]
            contract_id = contract["contract_id"]
            unit_price = contract["contract_price"]

        else:

            sku, _ = random.choice(
                PRODUCTS
            )

            contract_id = None
            unit_price = random_unit_price()

        quantity = random_quantity()

        po_date = random_date()

        po_amount = money(
            quantity * unit_price
        )

        records.append(
            {
                "po_id": f"PO-{index:06d}",
                "vendor_id": vendor["vendor_id"],
                "contract_id": contract_id,
                "sku": sku,
                "quantity": quantity,
                "unit_price": unit_price,
                "po_amount": po_amount,
                "po_date": po_date,
                "currency": "INR",
                "status": "APPROVED",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 4. GOODS RECEIPTS
# ============================================================

def generate_goods_receipts(
    purchase_orders: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index, po in purchase_orders.iterrows():

        po_quantity = int(
            po["quantity"]
        )

        received_quantity = po_quantity

        receipt_date = random_date_after(
            po["po_date"],
            60,
        )

        records.append(
            {
                "gr_id": f"GR-{index + 1:06d}",
                "po_id": po["po_id"],
                "vendor_id": po["vendor_id"],
                "sku": po["sku"],
                "ordered_quantity": po_quantity,
                "received_quantity": received_quantity,
                "receipt_date": receipt_date,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 5. INVOICES
# ============================================================

def generate_invoices(
    purchase_orders: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index in range(NUM_INVOICES):

        po = purchase_orders.iloc[
            index % len(purchase_orders)
        ]

        quantity = int(
            po["quantity"]
        )

        unit_price = float(
            po["unit_price"]
        )

        invoice_quantity = quantity

        invoice_unit_price = unit_price

        invoice_date = random_date_after(
            po["po_date"],
            90,
        )

        invoice_amount = money(
            invoice_quantity
            * invoice_unit_price
        )

        records.append(
            {
                "invoice_id": f"INV-{index + 1:07d}",
                "po_id": po["po_id"],
                "vendor_id": po["vendor_id"],
                "sku": po["sku"],
                "quantity": invoice_quantity,
                "unit_price": invoice_unit_price,
                "invoice_amount": invoice_amount,
                "invoice_date": invoice_date,
                "currency": "INR",
                "status": "PAID",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 6. PAYMENTS
# ============================================================

def generate_payments(
    invoices: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index, invoice in invoices.iterrows():

        payment_date = random_date_after(
            invoice["invoice_date"],
            30,
        )

        payment_amount = float(
            invoice["invoice_amount"]
        )

        records.append(
            {
                "payment_id": f"PAY-{index + 1:07d}",
                "invoice_id": invoice["invoice_id"],
                "vendor_id": invoice["vendor_id"],
                "payment_amount": money(
                    payment_amount
                ),
                "payment_date": payment_date,
                "payment_method": random.choice(
                    [
                        "BANK_TRANSFER",
                        "NEFT",
                        "RTGS",
                        "ACH",
                    ]
                ),
                "payment_status": "COMPLETED",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 7. REBATES
# ============================================================

def generate_rebates(
    vendors: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index in range(
        1,
        NUM_REBATES + 1,
    ):

        vendor = vendors.sample(
            1,
            random_state=SEED + index + 5000,
        ).iloc[0]

        eligible_amount = money(
            random.uniform(
                500000,
                10000000,
            )
        )

        rebate_percentage = random.choice(
            [2, 3, 5, 7, 10]
        )

        expected_rebate = money(
            eligible_amount
            * rebate_percentage
            / 100
        )

        actual_rebate = expected_rebate

        records.append(
            {
                "rebate_id": f"REB-{index:06d}",
                "vendor_id": vendor["vendor_id"],
                "eligible_spend": eligible_amount,
                "rebate_percentage": rebate_percentage,
                "expected_rebate": expected_rebate,
                "actual_rebate": actual_rebate,
                "status": "SETTLED",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# 8. CREDIT NOTES
# ============================================================

def generate_credit_notes(
    vendors: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for index in range(
        1,
        NUM_CREDIT_NOTES + 1,
    ):

        vendor = vendors.sample(
            1,
            random_state=SEED + index + 7000,
        ).iloc[0]

        credit_amount = money(
            random.uniform(
                5000,
                500000,
            )
        )

        records.append(
            {
                "credit_note_id": f"CN-{index:06d}",
                "vendor_id": vendor["vendor_id"],
                "credit_amount": credit_amount,
                "credit_date": random_date(),
                "status": "ISSUED",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# LEAKAGE INJECTION
# ============================================================

def inject_price_mismatch(
    invoices: pd.DataFrame,
    contracts: pd.DataFrame,
) -> tuple[pd.DataFrame, list]:

    invoices = invoices.copy()

    ground_truth = []

    eligible = invoices[
        invoices["invoice_id"].isin(
            invoices["invoice_id"].sample(
                min(
                    250,
                    len(invoices),
                ),
                random_state=SEED,
            )
        )
    ]

    for _, invoice in eligible.iterrows():

        contract_matches = contracts[
            (contracts["vendor_id"] == invoice["vendor_id"])
            & (contracts["sku"] == invoice["sku"])
        ]

        if len(contract_matches) == 0:
            continue

        contract = contract_matches.iloc[0]

        new_price = money(
            float(contract["contract_price"])
            * random.uniform(
                1.05,
                1.20,
            )
        )

        mask = (
            invoices["invoice_id"]
            == invoice["invoice_id"]
        )

        invoices.loc[
            mask,
            "unit_price"
        ] = new_price

        new_amount = money(
            invoice["quantity"]
            * new_price
        )

        invoices.loc[
            mask,
            "invoice_amount"
        ] = new_amount

        leakage = money(
            (
                new_price
                - float(contract["contract_price"])
            )
            * invoice["quantity"]
        )

        ground_truth.append(
            {
                "case_id": (
                    f"GT-PRICE-"
                    f"{invoice['invoice_id']}"
                ),
                "leakage_type": "PRICE_MISMATCH",
                "invoice_id": invoice["invoice_id"],
                "vendor_id": invoice["vendor_id"],
                "estimated_leakage": leakage,
            }
        )

    return invoices, ground_truth


def inject_duplicate_payments(
    payments: pd.DataFrame,
) -> tuple[pd.DataFrame, list]:

    payments = payments.copy()

    ground_truth = []

    sample_size = min(
        100,
        len(payments),
    )

    selected = payments.sample(
        sample_size,
        random_state=SEED + 900,
    )

    duplicates = selected.copy()

    duplicates["payment_id"] = (
        "PAY-DUP-"
        + duplicates["payment_id"]
        .str.replace("PAY-", "", regex=False)
    )

    duplicates["payment_date"] = (
        duplicates["payment_date"]
        + timedelta(days=1)
    )

    payments = pd.concat(
        [
            payments,
            duplicates,
        ],
        ignore_index=True,
    )

    for _, row in duplicates.iterrows():

        ground_truth.append(
            {
                "case_id": (
                    f"GT-DUP-"
                    f"{row['payment_id']}"
                ),
                "leakage_type": "DUPLICATE_PAYMENT",
                "invoice_id": row["invoice_id"],
                "vendor_id": row["vendor_id"],
                "estimated_leakage": row["payment_amount"],
            }
        )

    return payments, ground_truth


def inject_quantity_mismatch(
    invoices: pd.DataFrame,
    goods_receipts: pd.DataFrame,
) -> tuple[pd.DataFrame, list]:

    invoices = invoices.copy()

    ground_truth = []

    sample_size = min(
        100,
        len(invoices),
    )

    selected = invoices.sample(
        sample_size,
        random_state=SEED + 1000,
    )

    for _, invoice in selected.iterrows():

        gr_matches = goods_receipts[
            goods_receipts["po_id"]
            == invoice["po_id"]
        ]

        if len(gr_matches) == 0:
            continue

        gr = gr_matches.iloc[0]

        received_quantity = max(
            1,
            int(
                invoice["quantity"]
                * random.uniform(
                    0.70,
                    0.95,
                )
            ),
        )

        mask = (
            goods_receipts["gr_id"]
            == gr["gr_id"]
        )

        goods_receipts.loc[
            mask,
            "received_quantity"
        ] = received_quantity

        excess_quantity = max(
            0,
            int(invoice["quantity"])
            - received_quantity,
        )

        leakage = money(
            excess_quantity
            * invoice["unit_price"]
        )

        ground_truth.append(
            {
                "case_id": (
                    f"GT-QTY-"
                    f"{invoice['invoice_id']}"
                ),
                "leakage_type": "QUANTITY_MISMATCH",
                "invoice_id": invoice["invoice_id"],
                "vendor_id": invoice["vendor_id"],
                "estimated_leakage": leakage,
            }
        )

    return invoices, ground_truth


def inject_missing_rebates(
    rebates: pd.DataFrame,
) -> tuple[pd.DataFrame, list]:

    rebates = rebates.copy()

    ground_truth = []

    sample_size = min(
        75,
        len(rebates),
    )

    selected_indices = rebates.sample(
        sample_size,
        random_state=SEED + 1100,
    ).index

    for index in selected_indices:

        expected = float(
            rebates.loc[
                index,
                "expected_rebate",
            ]
        )

        actual = money(
            expected
            * random.uniform(
                0,
                0.40,
            )
        )

        rebates.loc[
            index,
            "actual_rebate"
        ] = actual

        leakage = money(
            expected - actual
        )

        ground_truth.append(
            {
                "case_id": (
                    f"GT-REB-"
                    f"{rebates.loc[index, 'rebate_id']}"
                ),
                "leakage_type": "MISSING_REBATE",
                "invoice_id": None,
                "vendor_id": rebates.loc[
                    index,
                    "vendor_id",
                ],
                "estimated_leakage": leakage,
            }
        )

    return rebates, ground_truth


# ============================================================
# SAVE DATA
# ============================================================

def save_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:

    path = OUTPUT_DIR / filename

    dataframe.to_csv(
        path,
        index=False,
    )

    print(
        f"Created: {path.name:<25} "
        f"{len(dataframe):>8,} rows"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("DOLLARGUARD AI - SYNTHETIC ENTERPRISE DATA GENERATOR")
    print("=" * 70)
    print()

    print("Generating vendors...")
    vendors = generate_vendors()

    print("Generating contracts...")
    contracts = generate_contracts(
        vendors
    )

    print("Generating purchase orders...")
    purchase_orders = generate_purchase_orders(
        vendors,
        contracts,
    )

    print("Generating goods receipts...")
    goods_receipts = generate_goods_receipts(
        purchase_orders
    )

    print("Generating invoices...")
    invoices = generate_invoices(
        purchase_orders
    )

    print("Generating payments...")
    payments = generate_payments(
        invoices
    )

    print("Generating rebates...")
    rebates = generate_rebates(
        vendors
    )

    print("Generating credit notes...")
    credit_notes = generate_credit_notes(
        vendors
    )

    print()
    print("Injecting known leakage scenarios...")

    invoices, price_truth = inject_price_mismatch(
        invoices,
        contracts,
    )

    payments, duplicate_truth = inject_duplicate_payments(
        payments
    )

    invoices, quantity_truth = inject_quantity_mismatch(
        invoices,
        goods_receipts,
    )

    rebates, rebate_truth = inject_missing_rebates(
        rebates
    )

    ground_truth = (
        price_truth
        + duplicate_truth
        + quantity_truth
        + rebate_truth
    )

    ground_truth_df = pd.DataFrame(
        ground_truth
    )

    # ========================================================
    # SAVE
    # ========================================================

    print()
    print("Saving datasets...")
    print("-" * 70)

    save_dataframe(
        vendors,
        "vendors.csv",
    )

    save_dataframe(
        contracts,
        "contracts.csv",
    )

    save_dataframe(
        purchase_orders,
        "purchase_orders.csv",
    )

    save_dataframe(
        goods_receipts,
        "goods_receipts.csv",
    )

    save_dataframe(
        invoices,
        "invoices.csv",
    )

    save_dataframe(
        payments,
        "payments.csv",
    )

    save_dataframe(
        rebates,
        "rebates.csv",
    )

    save_dataframe(
        credit_notes,
        "credit_notes.csv",
    )

    save_dataframe(
        ground_truth_df,
        "ground_truth.csv",
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("DATA GENERATION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Vendors              : {len(vendors):,}"
    )

    print(
        f"Contracts            : {len(contracts):,}"
    )

    print(
        f"Purchase Orders      : {len(purchase_orders):,}"
    )

    print(
        f"Goods Receipts       : {len(goods_receipts):,}"
    )

    print(
        f"Invoices             : {len(invoices):,}"
    )

    print(
        f"Payments             : {len(payments):,}"
    )

    print(
        f"Rebates              : {len(rebates):,}"
    )

    print(
        f"Credit Notes         : {len(credit_notes):,}"
    )

    print()
    print(
        f"Known leakage cases  : {len(ground_truth_df):,}"
    )

    if not ground_truth_df.empty:

        print()
        print("Ground-truth leakage breakdown:")
        print()

        breakdown = (
            ground_truth_df[
                "leakage_type"
            ]
            .value_counts()
        )

        for leakage_type, count in breakdown.items():

            print(
                f"  {leakage_type:<25} "
                f"{count:>5,}"
            )

    print()
    print(
        f"Output directory:"
        f"\n{OUTPUT_DIR}"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()