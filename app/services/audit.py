import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit_log(
    db: Session,
    action: str,
    username: Optional[str] = None,
    resource: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    details: Optional[Any] = None,
) -> AuditLog:
    if details is not None and not isinstance(details, str):
        details = json.dumps(details, default=str)

    entry = AuditLog(
        username=username,
        action=action,
        resource=resource,
        method=method,
        status_code=status_code,
        details=details,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry
