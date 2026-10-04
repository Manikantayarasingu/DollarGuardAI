from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database.connection import Base


class SystemInfo(Base):
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)

    application_name = Column(
        String(100),
        nullable=False
    )

    environment = Column(
        String(50),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )