from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.sla import SLACheckResultResponse, SLAStatsResponse
from app.schemas.ticket import TicketResponse
from app.services.sla_service import evaluate_and_notify_sla, get_sla_statistics
from app.services.ticket_service import to_ticket_response


router = APIRouter(
    prefix="/sla",
    tags=["SLA Monitoring & Overdue Alerts"],
    dependencies=[Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN]))],
)


@router.get(
    "/stats",
    response_model=SLAStatsResponse,
)
def get_sla_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Get campus SLA compliance metrics and overdue ticket count.
    Restricted to Admins and Superadmins.
    """
    return get_sla_statistics(db)


@router.get(
    "/overdue",
    response_model=list[TicketResponse],
)
def get_overdue_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Retrieve all unresolved tickets that have breached their SLA deadlines.
    Restricted to Admins and Superadmins.
    """
    now = datetime.now(timezone.utc)
    active_statuses = [
        TicketStatus.SUBMITTED.value,
        TicketStatus.UNDER_REVIEW.value,
        TicketStatus.ASSIGNED.value,
        TicketStatus.IN_PROGRESS.value,
        TicketStatus.REOPENED.value,
    ]

    overdue_tickets = db.scalars(
        select(Ticket)
        .where(
            Ticket.status.in_(active_statuses),
            Ticket.sla_deadline < now,
        )
        .order_by(Ticket.sla_deadline.asc())
    ).all()

    return [to_ticket_response(t) for t in overdue_tickets]


@router.post(
    "/check",
    response_model=SLACheckResultResponse,
)
def trigger_sla_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Manually triggers an SLA evaluation run and issues notifications for overdue/approaching tickets.
    Guarantees duplicate prevention.
    """
    return evaluate_and_notify_sla(db)
