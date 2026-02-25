from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select

from app.core.config import settings
from app.database.db_setup import SessionLocal
from app.models.audit_event import AuditEvent
from app.models.security_alert import SecurityAlert

logger = logging.getLogger(__name__)


def log_http_audit_event(
    *,
    event_type: str,
    actor_user_id: int | None,
    method: str,
    path: str,
    status_code: int,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
    metadata: dict | None = None,
) -> None:
    session = SessionLocal()
    try:
        event = AuditEvent(
            event_type=event_type,
            actor_user_id=actor_user_id,
            method=method,
            path=path,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata_json=metadata or {},
        )
        session.add(event)
        session.flush()
        _detect_and_create_alerts(session=session, event=event)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to persist audit event: %s", exc)
    finally:
        session.close()


def _detect_and_create_alerts(*, session, event: AuditEvent) -> None:
    now = datetime.now(timezone.utc)
    lookback_from = now - timedelta(minutes=settings.ALERT_LOOKBACK_MINUTES)
    dedup_from = now - timedelta(minutes=settings.ALERT_DEDUP_MINUTES)

    if event.event_type == "auth.login.failed" and event.ip_address:
        failures = _count_events(
            session=session,
            event_type="auth.login.failed",
            ip_address=event.ip_address,
            from_time=lookback_from,
        )
        if failures >= settings.ALERT_LOGIN_FAILURE_THRESHOLD:
            _create_alert_if_needed(
                session=session,
                rule_code="AUTH_BRUTE_FORCE_IP",
                severity="high",
                title="Possible brute force login attempts",
                description=(
                    f"{failures} failed login attempts from IP {event.ip_address} "
                    f"in the last {settings.ALERT_LOOKBACK_MINUTES} minute(s)."
                ),
                actor_user_id=event.actor_user_id,
                ip_address=event.ip_address,
                audit_event_id=event.id,
                dedup_from=dedup_from,
            )

    if event.event_type == "auth.access.denied":
        denied_count = _count_events(
            session=session,
            event_type="auth.access.denied",
            actor_user_id=event.actor_user_id,
            ip_address=event.ip_address,
            from_time=lookback_from,
        )
        if denied_count >= settings.ALERT_ACCESS_DENIED_THRESHOLD:
            _create_alert_if_needed(
                session=session,
                rule_code="EXCESSIVE_FORBIDDEN_REQUESTS",
                severity="medium",
                title="Excessive forbidden requests detected",
                description=(
                    f"{denied_count} forbidden requests detected in the last "
                    f"{settings.ALERT_LOOKBACK_MINUTES} minute(s)."
                ),
                actor_user_id=event.actor_user_id,
                ip_address=event.ip_address,
                audit_event_id=event.id,
                dedup_from=dedup_from,
            )


def _count_events(
    *,
    session,
    event_type: str,
    from_time: datetime,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> int:
    predicates = [AuditEvent.event_type == event_type, AuditEvent.occurred_at >= from_time]
    if actor_user_id is not None:
        predicates.append(AuditEvent.actor_user_id == actor_user_id)
    if ip_address:
        predicates.append(AuditEvent.ip_address == ip_address)
    stmt = select(func.count(AuditEvent.id)).where(and_(*predicates))
    return int(session.execute(stmt).scalar_one() or 0)


def _create_alert_if_needed(
    *,
    session,
    rule_code: str,
    severity: str,
    title: str,
    description: str,
    actor_user_id: int | None,
    ip_address: str | None,
    audit_event_id: int | None,
    dedup_from: datetime,
) -> None:
    predicates = [
        SecurityAlert.rule_code == rule_code,
        SecurityAlert.acknowledged.is_(False),
        SecurityAlert.created_at >= dedup_from,
    ]
    if actor_user_id is not None:
        predicates.append(SecurityAlert.actor_user_id == actor_user_id)
    else:
        predicates.append(SecurityAlert.actor_user_id.is_(None))
    if ip_address:
        predicates.append(SecurityAlert.ip_address == ip_address)
    else:
        predicates.append(SecurityAlert.ip_address.is_(None))

    exists_stmt = select(SecurityAlert.id).where(and_(*predicates)).limit(1)
    existing = session.execute(exists_stmt).scalar_one_or_none()
    if existing:
        return

    alert = SecurityAlert(
        rule_code=rule_code,
        severity=severity,
        title=title,
        description=description,
        actor_user_id=actor_user_id,
        ip_address=ip_address,
        audit_event_id=audit_event_id,
    )
    session.add(alert)
    logger.warning("Security alert generated: %s", rule_code)
