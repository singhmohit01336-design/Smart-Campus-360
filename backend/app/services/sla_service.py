from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.sla import SLACheckResultResponse, SLAStatsResponse


def get_sla_statistics(db: Session) -> SLAStatsResponse:
    """Calculate real-time SLA metrics for active tickets."""
    now = datetime.now(timezone.utc)
    active_statuses = [
        TicketStatus.SUBMITTED.value,
        TicketStatus.UNDER_REVIEW.value,
        TicketStatus.ASSIGNED.value,
        TicketStatus.IN_PROGRESS.value,
        TicketStatus.REOPENED.value,
    ]

    active_tickets = db.scalars(
        select(Ticket).where(Ticket.status.in_(active_statuses))
    ).all()

    total_active = len(active_tickets)
    if total_active == 0:
        return SLAStatsResponse(
            total_active_tickets=0,
            on_time_tickets=0,
            approaching_deadline_tickets=0,
            overdue_tickets=0,
            sla_compliance_rate=100.0,
        )

    overdue_count = 0
    approaching_count = 0
    on_time_count = 0

    approaching_window = now + timedelta(hours=2)

    for t in active_tickets:
        if not t.sla_deadline:
            on_time_count += 1
            continue

        if t.sla_deadline < now:
            overdue_count += 1
        elif now <= t.sla_deadline <= approaching_window:
            approaching_count += 1
        else:
            on_time_count += 1

    compliance_rate = round(((total_active - overdue_count) / total_active) * 100.0, 2)

    return SLAStatsResponse(
        total_active_tickets=total_active,
        on_time_tickets=on_time_count,
        approaching_deadline_tickets=approaching_count,
        overdue_tickets=overdue_count,
        sla_compliance_rate=compliance_rate,
    )


def evaluate_and_notify_sla(db: Session) -> SLACheckResultResponse:
    """
    Evaluates active tickets against SLA deadlines.
    Creates notifications for assigned technicians and administrators.
    Guarantees idempotency and avoids duplicate notifications.
    """
    now = datetime.now(timezone.utc)
    active_statuses = [
        TicketStatus.SUBMITTED.value,
        TicketStatus.UNDER_REVIEW.value,
        TicketStatus.ASSIGNED.value,
        TicketStatus.IN_PROGRESS.value,
        TicketStatus.REOPENED.value,
    ]

    active_tickets = db.scalars(
        select(Ticket).where(Ticket.status.in_(active_statuses))
    ).all()

    # Pre-fetch campus administrators
    admins = db.scalars(
        select(User).where(
            User.role.in_([UserRole.ADMIN.value, UserRole.SUPERADMIN.value]),
            User.is_active == True,
        )
    ).all()

    overdue_detected = 0
    approaching_detected = 0
    notifications_created = 0
    notifications_skipped = 0

    approaching_window = now + timedelta(hours=2)

    for t in active_tickets:
        if not t.sla_deadline:
            continue

        alert_type = None
        alert_tag = None
        alert_title = None
        alert_msg = None

        if t.sla_deadline < now:
            overdue_detected += 1
            alert_type = "sla_alert"
            alert_tag = "[OVERDUE]"
            alert_title = f"SLA Breach: Ticket {t.ticket_number} Overdue"
            alert_msg = f"{alert_tag} Ticket {t.ticket_number} ('{t.title}') exceeded its SLA deadline on {t.sla_deadline.strftime('%Y-%m-%d %H:%M UTC')}."
        elif now <= t.sla_deadline <= approaching_window:
            approaching_detected += 1
            alert_type = "sla_alert"
            alert_tag = "[APPROACHING]"
            alert_title = f"SLA Warning: Ticket {t.ticket_number} Near Deadline"
            alert_msg = f"{alert_tag} Ticket {t.ticket_number} ('{t.title}') is due within 2 hours ({t.sla_deadline.strftime('%Y-%m-%d %H:%M UTC')})."

        if not alert_tag:
            continue

        # Target recipients: assigned technician + admins
        target_users = list(admins)
        if t.assigned_to_id:
            assigned_tech = db.get(User, t.assigned_to_id)
            if assigned_tech and assigned_tech not in target_users:
                target_users.append(assigned_tech)

        for user in target_users:
            # Check duplicate alert prevention: has this user received this exact alert tag for this ticket?
            existing_alert = db.scalar(
                select(Notification.id).where(
                    Notification.user_id == user.id,
                    Notification.notification_type == alert_type,
                    Notification.message.like(f"%{alert_tag}%{t.ticket_number}%"),
                )
            )

            if existing_alert:
                notifications_skipped += 1
            else:
                notification = Notification(
                    user_id=user.id,
                    title=alert_title,
                    message=alert_msg,
                    notification_type=alert_type,
                    is_read=False,
                )
                db.add(notification)
                notifications_created += 1

    db.commit()

    return SLACheckResultResponse(
        evaluated_tickets=len(active_tickets),
        overdue_detected=overdue_detected,
        approaching_detected=approaching_detected,
        notifications_created=notifications_created,
        notifications_skipped_duplicate=notifications_skipped,
    )
