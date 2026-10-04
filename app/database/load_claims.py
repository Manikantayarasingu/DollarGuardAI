"""
DollarGuard AI - Claim Management Loader

Imports the unified leakage detection results into the
claims database table.
"""

import os

import pandas as pd

from app.database.connection import SessionLocal
from app.database.init_db import initialize_database
from app.models.claim import Claim


INPUT_FILE = (
    "data/processed/unified_claims.csv"
)


def load_claims():

    if not os.path.exists(INPUT_FILE):

        print(
            f"\nERROR: Claims file not found:"
        )

        print(
            f"  {INPUT_FILE}"
        )

        print(
            "\nRun the leakage engine first:"
        )

        print(
            "python -m app.services.leakage_engine"
        )

        return

    initialize_database()

    df = pd.read_csv(
        INPUT_FILE
    )

    if df.empty:

        print(
            "\nNo claims available to load."
        )

        return

    session = SessionLocal()

    try:

        inserted = 0
        updated = 0

        for _, row in df.iterrows():

            claim_id = str(
                row["claim_id"]
            )

            existing = (
                session.query(Claim)
                .filter(
                    Claim.claim_id
                    == claim_id
                )
                .first()
            )

            if existing:

                existing.leakage_type = (
                    row.get(
                        "leakage_type"
                    )
                )

                existing.vendor_id = (
                    row.get(
                        "vendor_id"
                    )
                )

                existing.invoice_id = (
                    row.get(
                        "invoice_id"
                    )
                )

                existing.po_id = (
                    row.get(
                        "po_id"
                    )
                )

                existing.contract_id = (
                    row.get(
                        "contract_id"
                    )
                )

                existing.rebate_id = (
                    row.get(
                        "rebate_id"
                    )
                )

                existing.sku = (
                    row.get(
                        "sku"
                    )
                )

                existing.original_amount = (
                    row.get(
                        "original_amount"
                    )
                )

                existing.expected_amount = (
                    row.get(
                        "expected_amount"
                    )
                )

                existing.potential_leakage = (
                    row.get(
                        "potential_leakage",
                        0,
                    )
                )

                existing.confidence_score = (
                    row.get(
                        "confidence_score"
                    )
                )

                existing.risk_level = (
                    row.get(
                        "risk_level"
                    )
                )

                existing.currency = (
                    row.get(
                        "currency",
                        "INR",
                    )
                )

                existing.evidence = (
                    row.get(
                        "evidence"
                    )
                )

                updated += 1

            else:

                claim = Claim(

                    claim_id=claim_id,

                    leakage_type=row.get(
                        "leakage_type"
                    ),

                    vendor_id=row.get(
                        "vendor_id"
                    ),

                    invoice_id=row.get(
                        "invoice_id"
                    ),

                    po_id=row.get(
                        "po_id"
                    ),

                    contract_id=row.get(
                        "contract_id"
                    ),

                    rebate_id=row.get(
                        "rebate_id"
                    ),

                    sku=row.get(
                        "sku"
                    ),

                    original_amount=row.get(
                        "original_amount"
                    ),

                    expected_amount=row.get(
                        "expected_amount"
                    ),

                    potential_leakage=row.get(
                        "potential_leakage",
                        0,
                    ),

                    confidence_score=row.get(
                        "confidence_score"
                    ),

                    risk_level=row.get(
                        "risk_level"
                    ),

                    currency=row.get(
                        "currency",
                        "INR",
                    ),

                    evidence=row.get(
                        "evidence"
                    ),

                    status="NEW",
                )

                session.add(
                    claim
                )

                inserted += 1

        session.commit()

        print(
            "\n" + "=" * 70
        )

        print(
            "DOLLARGUARD AI - CLAIM LOADER"
        )

        print(
            "=" * 70
        )

        print(
            f"\nSource claims : {len(df):,}"
        )

        print(
            f"Inserted      : {inserted:,}"
        )

        print(
            f"Updated       : {updated:,}"
        )

        total_claims = (
            session.query(
                Claim
            ).count()
        )

        print(
            f"Database total: {total_claims:,}"
        )

        print(
            "\nClaims loaded successfully."
        )

        print(
            "=" * 70
        )

    except Exception as error:

        session.rollback()

        print(
            "\nERROR loading claims:"
        )

        print(
            error
        )

    finally:

        session.close()


if __name__ == "__main__":

    load_claims()