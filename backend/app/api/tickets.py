import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.category import Category
from app.models.department import Department
from app.models.history import TicketHistory
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.schemas.history import HistoryResponse
from app.schemas.ticket import (
    PaginatedTicketsResponse,
    TicketAssignRequest,
    TicketCreate,
    TicketResponse,
    TicketStatusUpdateRequest,
)
from app.services.ticket_service import (
    calculate_sla_deadline,
    check_ticket_access,
    generate_ticket_number,
    to_ticket_response,
    validate_status_transition,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets & Complaints"],
)


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPERADMIN])
    ),
):
    """
    Create a new complaint/service ticket.
    Accessible to authenticated Students, Faculty, Admins, and Superadmins.
    Technicians are restricted from creating tickets.
    """
    # 1. Validate department
    dept = db.get(Department, ticket_in.department_id)
    if not dept or not dept.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified department does not exist or is inactive.",
        )

    # 2. Validate category and department association
    cat = db.get(Category, ticket_in.category_id)
    if not cat or not cat.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified category does not exist or is inactive.",
        )
    if cat.department_id != dept.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category does not belong to the selected department.",
        )

    # 3. Generate unique ticket number and calculate SLA
    ticket_number = generate_ticket_number(db)
    sla_deadline = calculate_sla_deadline(ticket_in.priority.value)

    # 4. Create Ticket record
    ticket = Ticket(
        ticket_number=ticket_number,
        title=ticket_in.title,
        description=ticket_in.description,
        category_id=ticket_in.category_id,
        department_id=ticket_in.department_id,
        created_by_id=current_user.id,
        location=ticket_in.location,
        building=ticket_in.building,
        room_number=ticket_in.room_number,
        qr_code_identifier=ticket_in.qr_code_identifier,
        priority=ticket_in.priority.value,
        status=TicketStatus.SUBMITTED.value,
        sla_deadline=sla_deadline,
    )
    db.add(ticket)
    db.flush()

    # 5. Record initial status history
    initial_history = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=current_user.id,
        old_status=None,
        new_status=TicketStatus.SUBMITTED.value,
        remarks="Ticket submitted by creator.",
    )
    db.add(initial_history)
    db.commit()
    db.refresh(ticket)

    return to_ticket_response(ticket)


@router.get(
    "/",
    response_model=PaginatedTicketsResponse,
)
def list_tickets(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search ticket number, title, or description"),
    status: str | None = Query(default=None, description="Filter by status"),
    priority: str | None = Query(default=None, description="Filter by priority"),
    category_id: int | None = Query(default=None, description="Filter by category ID"),
    department_id: int | None = Query(default=None, description="Filter by department ID"),
    start_date: datetime | None = Query(default=None, description="Filter tickets created on or after"),
    end_date: datetime | None = Query(default=None, description="Filter tickets created on or before"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List tickets with search, filtering, and pagination.
    Enforces role-based visibility:
    - Students and Faculty: view only tickets they created.
    - Technicians: view only tickets assigned to them.
    - Admin and Superadmin: view all campus tickets.
    """
    query = select(Ticket)

    # Role-based visibility scoping
    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else str(current_user.role).lower()
    )

    if user_role in {UserRole.STUDENT.value, UserRole.FACULTY.value}:
        query = query.where(Ticket.created_by_id == current_user.id)
    elif user_role == UserRole.TECHNICIAN.value:
        query = query.where(Ticket.assigned_to_id == current_user.id)
    # Admin and Superadmin can access all tickets

    # Search filter
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Ticket.ticket_number.ilike(search_pattern),
                Ticket.title.ilike(search_pattern),
                Ticket.description.ilike(search_pattern),
                Ticket.location.ilike(search_pattern),
            )
        )

    # Attribute filters
    if status:
        query = query.where(Ticket.status == status.lower())
    if priority:
        query = query.where(Ticket.priority == priority.lower())
    if category_id:
        query = query.where(Ticket.category_id == category_id)
    if department_id:
        query = query.where(Ticket.department_id == department_id)
    if start_date:
        query = query.where(Ticket.created_at >= start_date)
    if end_date:
        query = query.where(Ticket.created_at <= end_date)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    # Pagination and sorting
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    query = (
        query.options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.department),
        )
        .order_by(Ticket.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    tickets = db.scalars(query).unique().all()
    items = [to_ticket_response(t) for t in tickets]

    return PaginatedTicketsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve single ticket details.
    Enforces authorization check based on user role and assignment.
    """
    ticket = db.scalar(
        select(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.department),
        )
        .where(Ticket.id == ticket_id)
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)
    return to_ticket_response(ticket)


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_ticket(
    ticket_id: int,
    payload: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Assign a ticket to an active technician.
    Restricted to Admins and Superadmins.
    """
    ticket = db.scalar(
        select(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.department),
        )
        .where(Ticket.id == ticket_id)
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    # Validate technician existence, role, and active status
    technician = db.get(User, payload.technician_id)
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Technician with user ID {payload.technician_id} not found.",
        )

    tech_role = (
        technician.role.value
        if isinstance(technician.role, UserRole)
        else str(technician.role).lower()
    )
    if tech_role != UserRole.TECHNICIAN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {technician.email} is not a technician (role is '{tech_role}').",
        )

    if not technician.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Technician account {technician.email} is inactive.",
        )

    old_status = ticket.status
    ticket.assigned_to_id = technician.id

    # Automatically advance submitted or under_review tickets to assigned
    if ticket.status in {TicketStatus.SUBMITTED.value, TicketStatus.UNDER_REVIEW.value}:
        ticket.status = TicketStatus.ASSIGNED.value

    # Record assignment in ticket history
    history_entry = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=current_user.id,
        old_status=old_status,
        new_status=ticket.status,
        remarks=f"Ticket assigned to technician: {technician.full_name} ({technician.email}).",
    )
    db.add(history_entry)
    db.commit()
    db.refresh(ticket)

    return to_ticket_response(ticket)


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update ticket workflow status with validation and history logging.
    Enforces role-based status lifecycle constraints.
    """
    ticket = db.scalar(
        select(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.department),
        )
        .where(Ticket.id == ticket_id)
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    # Validate lifecycle transition rules and user authorization
    validate_status_transition(ticket, payload.status, current_user)

    old_status = ticket.status
    ticket.status = payload.status.value

    # Set or clear resolved_at timestamp
    if payload.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.now(timezone.utc)
    elif payload.status == TicketStatus.REOPENED:
        ticket.resolved_at = None

    # Record status change in immutable ticket history
    remarks_text = payload.remarks or f"Status changed from {old_status} to {payload.status.value}."
    history_entry = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=current_user.id,
        old_status=old_status,
        new_status=payload.status.value,
        remarks=remarks_text,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(ticket)

    return to_ticket_response(ticket)


@router.get(
    "/{ticket_id}/history",
    response_model=list[HistoryResponse],
)
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve chronological audit history for a ticket.
    Access is restricted to authorized ticket stakeholders.
    """
    ticket = db.scalar(
        select(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.department),
        )
        .where(Ticket.id == ticket_id)
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    history_records = db.scalars(
        select(TicketHistory)
        .options(joinedload(TicketHistory.changed_by))
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
    ).all()

    results = []
    for h in history_records:
        changed_name = h.changed_by.full_name if h.changed_by else None
        changed_role = h.changed_by.role if h.changed_by else None
        results.append(
            HistoryResponse(
                id=h.id,
                ticket_id=h.ticket_id,
                changed_by_id=h.changed_by_id,
                old_status=h.old_status,
                new_status=h.new_status,
                remarks=h.remarks,
                created_at=h.created_at,
                changed_by_name=changed_name,
                changed_by_role=changed_role,
            )
        )
    return results
