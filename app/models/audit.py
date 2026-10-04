from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.connection import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(200), nullable=True)
    method = Column(String(20), nullable=True)
    status_code = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
