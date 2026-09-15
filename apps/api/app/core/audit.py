"""Audit logging. Sensitive operations are recorded with actor + outcome.
Secrets, password hashes, email/CV contents are never logged."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog


def record(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str = "",
    entity_id: int | None = None,
    ip: str = "",
    outcome: str = "OK",
    detail: str = "",
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action[:120],
            entity_type=entity_type[:80],
            entity_id=entity_id,
            ip=(ip or "")[:64],
            outcome=outcome[:16],
            detail=detail[:500],
        )
    )
    db.commit()