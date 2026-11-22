from datetime import datetime, timedelta, timezone
import secrets
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.schemas.ticket import TicketResponse


SLA_HOURS = {
    TicketPriority.CRITICAL.value: 4,
    TicketPriority.HIGH.value: 12,
    TicketPriority.MEDIUM.value: 24,
    TicketPriority.LOW.value: 72,
}


def calculate_sla_deadline(priority: str) -> datetime:
    """Calculate SLA deadline timestamp based on ticket priority."""
    hours = SLA_HOURS.get(priority.lower(), 24)
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def generate_ticket_number(db: Session) -> str:
    """Generate a guaranteed unique ticket number (e.g., TCK-20261122-A1B2)."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        hex_suffix = secrets.token_hex(2).upper()
        candidate = f"TCK-{date_str}-{hex_suffix}"
        exists = db.scalar(
            select(Ticket.id).where(Ticket.ticket_number == candidate)
        )
        if not exists:
            return candidate

    # Fallback with longer suffix in rare collision case
    hex_suffix = secrets.token_hex(4).upper()
    return f"TCK-{date_str}-{hex_suffix}"


def check_ticket_access(ticket: Ticket, user: User) -> None:
    """Verify that current user is authorized to view or interact with this ticket."""
    user_role = user.role.value if isinstance(user.role, UserRole) else str(user.role).lower()

    if user_role in {UserRole.SUPERADMIN.value, UserRole.ADMIN.value}:
        return

    if user_role == UserRole.TECHNICIAN.value:
        if ticket.assigned_to_id == user.id or ticket.created_by_id == user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you are not assigned to this ticket",
        )

    # Students and faculty can only view tickets they created
    if ticket.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you are not authorized to access this ticket",
        )


def validate_status_transition(
    ticket: Ticket,
    new_status: TicketStatus,
    user: User,
) -> None:
    """
    Enforces valid business lifecycle transitions and role-based status permissions.
    """
    user_role = user.role.value if isinstance(user.role, UserRole) else str(user.role).lower()
    curr = ticket.status
    target = new_status.value

    if curr == target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket is already in '{curr}' status.",
        )

    # 1. Students and Faculty workflow permissions
    if user_role in {UserRole.STUDENT.value, UserRole.FACULTY.value}:
        if ticket.created_by_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot update status on tickets you did not create.",
            )
        # Student/Faculty can close a resolved/submitted ticket, or reopen a resolved/closed ticket
        allowed_student_transitions = {
            TicketStatus.RESOLVED.value: {TicketStatus.CLOSED.value, TicketStatus.REOPENED.value},
            TicketStatus.CLOSED.value: {TicketStatus.REOPENED.value},
            TicketStatus.SUBMITTED.value: {TicketStatus.CLOSED.value},
        }
        allowed_targets = allowed_student_transitions.get(curr, set())
        if target not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Students and faculty cannot transition ticket from '{curr}' to '{target}'.",
            )
        return

    # 2. Technician workflow permissions
    if user_role == UserRole.TECHNICIAN.value:
        if ticket.assigned_to_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Technicians can only update status on tickets assigned to them.",
            )
        allowed_tech_transitions = {
            TicketStatus.ASSIGNED.value: {TicketStatus.IN_PROGRESS.value},
            TicketStatus.IN_PROGRESS.value: {TicketStatus.RESOLVED.value},
            TicketStatus.REOPENED.value: {TicketStatus.IN_PROGRESS.value},
        }
        allowed_targets = allowed_tech_transitions.get(curr, set())
        if target not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Technicians cannot transition ticket from '{curr}' to '{target}'.",
            )
        return

    # 3. Admin & Superadmin lifecycle workflow
    admin_lifecycle = {
        TicketStatus.SUBMITTED.value: {
            TicketStatus.UNDER_REVIEW.value,
            TicketStatus.ASSIGNED.value,
            TicketStatus.CLOSED.value,
        },
        TicketStatus.UNDER_REVIEW.value: {
            TicketStatus.ASSIGNED.value,
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.CLOSED.value,
        },
        TicketStatus.ASSIGNED.value: {
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.RESOLVED.value,
            TicketStatus.UNDER_REVIEW.value,
            TicketStatus.CLOSED.value,
        },
        TicketStatus.IN_PROGRESS.value: {
            TicketStatus.RESOLVED.value,
            TicketStatus.ASSIGNED.value,
            TicketStatus.UNDER_REVIEW.value,
            TicketStatus.CLOSED.value,
        },
        TicketStatus.RESOLVED.value: {
            TicketStatus.CLOSED.value,
            TicketStatus.REOPENED.value,
        },
        TicketStatus.CLOSED.value: {
            TicketStatus.REOPENED.value,
        },
        TicketStatus.REOPENED.value: {
            TicketStatus.ASSIGNED.value,
            TicketStatus.IN_PROGRESS.value,
            TicketStatus.UNDER_REVIEW.value,
            TicketStatus.CLOSED.value,
        },
    }
    allowed_admin_targets = admin_lifecycle.get(curr, set())
    if target not in allowed_admin_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ticket status transition from '{curr}' to '{target}'.",
        )


def to_ticket_response(ticket: Ticket) -> TicketResponse:
    """Build a rich TicketResponse schema including denormalized relation metadata."""
    creator_name = ticket.creator.full_name if ticket.creator else None
    creator_email = ticket.creator.email if ticket.creator else None
    assignee_name = ticket.assignee.full_name if ticket.assignee else None
    category_name = ticket.category.category_name if ticket.category else None
    department_name = ticket.department.department_name if ticket.department else None

    return TicketResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        category_id=ticket.category_id,
        department_id=ticket.department_id,
        created_by_id=ticket.created_by_id,
        assigned_to_id=ticket.assigned_to_id,
        location=ticket.location,
        building=ticket.building,
        room_number=ticket.room_number,
        qr_code_identifier=ticket.qr_code_identifier,
        priority=ticket.priority,
        status=ticket.status,
        sla_deadline=ticket.sla_deadline,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        creator_name=creator_name,
        creator_email=creator_email,
        assignee_name=assignee_name,
        category_name=category_name,
        department_name=department_name,
    )
