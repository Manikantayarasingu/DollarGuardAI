from pathlib import Path

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parents[1]

CONTRACT_DATA = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "contracts.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "documents"
    / "contracts"
)


def clean_value(value, default="N/A"):
    if pd.isna(value):
        return default

    return str(value)


def generate_contract_pdf(row, output_path):
    pdf = canvas.Canvas(
        str(output_path),
        pagesize=A4
    )

    width, height = A4

    y = height - 60

    def write_line(text, spacing=18):
        nonlocal y

        if y < 60:
            pdf.showPage()
            y = height - 60

        pdf.drawString(
            60,
            y,
            str(text)
        )

        y -= spacing

    pdf.setTitle(
        f"Supplier Contract - "
        f"{clean_value(row.get('contract_id'))}"
    )

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    write_line(
        "SUPPLIER MASTER CONTRACT",
        25
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    write_line(
        "DollarGuard AI Synthetic Enterprise Contract"
    )

    write_line(
        ""
    )

    contract_id = clean_value(
        row.get("contract_id")
    )

    vendor_id = clean_value(
        row.get("vendor_id")
    )

    write_line(
        f"Contract ID: {contract_id}"
    )

    write_line(
        f"Vendor ID: {vendor_id}"
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "1. COMMERCIAL TERMS",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    unit_price = clean_value(
        row.get("unit_price"),
        "0"
    )

    write_line(
        f"Unit Price: INR {unit_price}"
    )

    currency = clean_value(
        row.get("currency"),
        "INR"
    )

    write_line(
        f"Currency: {currency}"
    )

    rebate = clean_value(
        row.get("rebate_percentage"),
        "0"
    )

    write_line(
        f"Volume Rebate: {rebate}%"
    )

    volume = clean_value(
        row.get("volume_commitment"),
        "0"
    )

    write_line(
        f"Minimum Volume Commitment: {volume} units"
    )

    payment_terms = clean_value(
        row.get("payment_terms"),
        "Net 30"
    )

    write_line(
        f"Payment Terms: {payment_terms}"
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "2. DELIVERY AND PENALTIES",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    penalty = clean_value(
        row.get("penalty_percentage"),
        "0"
    )

    write_line(
        f"Late Delivery Penalty: {penalty}%"
    )

    write_line(
        "Supplier shall be responsible for applicable "
        "commercial penalties for non-compliance."
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "3. CONTRACT PERIOD",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    start_date = clean_value(
        row.get("start_date")
    )

    end_date = clean_value(
        row.get("end_date")
    )

    write_line(
        f"Effective Date: {start_date}"
    )

    write_line(
        f"Expiry Date: {end_date}"
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "4. REBATE CLAUSE",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    write_line(
        f"The supplier shall provide a "
        f"{rebate}% rebate based on applicable "
        "contractual volume commitments."
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "5. PAYMENT CLAUSE",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    write_line(
        f"Payment shall be made according to "
        f"the agreed {payment_terms} terms."
    )

    write_line(
        ""
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    write_line(
        "6. TERMINATION AND RENEWAL",
        22
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    write_line(
        "The agreement may be terminated according "
        "to the applicable contractual notice period."
    )

    write_line(
        "Renewal shall be subject to contractual review."
    )

    write_line(
        ""
    )

    write_line(
        "This document is synthetic data generated "
        "for the DollarGuard AI portfolio project."
    )

    pdf.save()


def main():

    print()
    print("=" * 70)
    print(
        "DOLLARGUARD AI - "
        "SYNTHETIC CONTRACT DOCUMENT GENERATOR"
    )
    print("=" * 70)
    print()

    if not CONTRACT_DATA.exists():
        raise FileNotFoundError(
            f"Contract dataset not found:\n"
            f"{CONTRACT_DATA}"
        )

    contracts = pd.read_csv(
        CONTRACT_DATA
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        f"Contracts found: {len(contracts):,}"
    )

    print()

    generated = 0

    for _, row in contracts.iterrows():

        contract_id = clean_value(
            row.get("contract_id"),
            f"CONTRACT-{generated + 1}"
        )

        filename = (
            f"{contract_id}.pdf"
        )

        output_path = (
            OUTPUT_DIR
            / filename
        )

        generate_contract_pdf(
            row,
            output_path
        )

        generated += 1

        if generated <= 10:
            print(
                f"Created: {filename}"
            )

    print()

    print("=" * 70)
    print("CONTRACT DOCUMENT GENERATION COMPLETE")
    print("=" * 70)
    print()

    print(
        f"PDF documents created: "
        f"{generated:,}"
    )

    print()

    print(
        f"Location:"
    )

    print(
        f"  {OUTPUT_DIR}"
    )

    print()


if __name__ == "__main__":
    main()