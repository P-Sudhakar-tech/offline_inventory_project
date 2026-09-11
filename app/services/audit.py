from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import AuditLog
from app.security.session_context import current_user_id


def log_action(session: Session, action: str, details: str | None = None) -> AuditLog:
    entry = AuditLog(user_id=current_user_id(), action=action, details=details)
    session.add(entry)
    session.flush()
    return entry


def recent_audit_log(session: Session, limit: int = 100):
    from app.data.models import User

    stmt = (
        select(AuditLog, User)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
    )
    return session.execute(stmt).all()
