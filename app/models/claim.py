from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database.connection import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    claim_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    leakage_type = Column(
        String(100),
        nullable=False,
        index=True,
    )

    vendor_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    invoice_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    po_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    contract_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    rebate_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    sku = Column(
        String(100),
        nullable=True,
    )

    original_amount = Column(
        Float,
        nullable=True,
    )

    expected_amount = Column(
        Float,
        nullable=True,
    )

    potential_leakage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    recovered_amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    confidence_score = Column(
        Float,
        nullable=True,
    )

    risk_level = Column(
        String(30),
        nullable=True,
        index=True,
    )

    currency = Column(
        String(10),
        nullable=True,
        default="INR",
    )

    evidence = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="NEW",
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )