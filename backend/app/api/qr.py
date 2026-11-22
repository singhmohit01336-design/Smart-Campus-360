from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.category import Category
from app.models.department import Department
from app.models.history import TicketHistory
from app.models.location import CampusLocation
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.schemas.location import CampusLocationResponse, QRTicketCreate
from app.schemas.ticket import TicketResponse
from app.services.ticket_service import (
    calculate_sla_deadline,
    generate_ticket_number,
    to_ticket_response,
)


router = APIRouter(
    prefix="/qr",
    tags=["QR Code & Classroom Reporting"],
)


@router.get(
    "/locations",
    response_model=list[CampusLocationResponse],
)
def list_campus_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all registered and active campus locations with QR codes for quick reporting.
    """
    locations = (
        db.scalars(
            select(CampusLocation)
            .where(CampusLocation.is_active == True)
            .order_by(CampusLocation.building.asc(), CampusLocation.room_number.asc())
        )
        .unique()
        .all()
    )

    results = []
    for loc in locations:
        dept_name = loc.department.department_name if loc.department else None
        results.append(
            CampusLocationResponse(
                id=loc.id,
                qr_code_identifier=loc.qr_code_identifier,
                building=loc.building,
                room_number=loc.room_number,
                floor=loc.floor,
                location_name=loc.location_name,
                department_id=loc.department_id,
                department_name=dept_name,
                is_active=loc.is_active,
            )
        )
    return results


@router.get(
    "/{qr_code_identifier}",
    response_model=CampusLocationResponse,
)
def resolve_qr_location(
    qr_code_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Resolve a physical QR code identifier into verified classroom / lab location metadata.
    """
    location = db.scalar(
        select(CampusLocation).where(
            CampusLocation.qr_code_identifier == qr_code_identifier.strip(),
            CampusLocation.is_active == True,
        )
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campus location with QR identifier '{qr_code_identifier}' not found or inactive.",
        )

    dept_name = location.department.department_name if location.department else None

    return CampusLocationResponse(
        id=location.id,
        qr_code_identifier=location.qr_code_identifier,
        building=location.building,
        room_number=location.room_number,
        floor=location.floor,
        location_name=location.location_name,
        department_id=location.department_id,
        department_name=dept_name,
        is_active=location.is_active,
    )


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_qr_complaint(
    payload: QRTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a complaint via QR code. Automatically binds building, room number,
    and verified location metadata to the new service ticket.
    """
    # 1. Resolve QR location
    location = db.scalar(
        select(CampusLocation).where(
            CampusLocation.qr_code_identifier == payload.qr_code_identifier.strip(),
            CampusLocation.is_active == True,
        )
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid or inactive QR code identifier '{payload.qr_code_identifier}'.",
        )

    # 2. Determine target department
    dept_id = payload.department_id or location.department_id
    if not dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required as location has no default department.",
        )

    dept = db.get(Department, dept_id)
    if not dept or not dept.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified department does not exist or is inactive.",
        )

    # 3. Validate category
    cat = db.get(Category, payload.category_id)
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

    # 4. Generate unique ticket number and SLA
    ticket_number = generate_ticket_number(db)
    sla_deadline = calculate_sla_deadline(payload.priority.value)

    # 5. Create Ticket with location metadata automatically populated
    ticket = Ticket(
        ticket_number=ticket_number,
        title=payload.title,
        description=payload.description,
        category_id=payload.category_id,
        department_id=dept.id,
        created_by_id=current_user.id,
        location=location.location_name,
        building=location.building,
        room_number=location.room_number,
        qr_code_identifier=location.qr_code_identifier,
        priority=payload.priority.value,
        status=TicketStatus.SUBMITTED.value,
        sla_deadline=sla_deadline,
    )
    db.add(ticket)
    db.flush()

    # 6. Record status history
    initial_history = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=current_user.id,
        old_status=None,
        new_status=TicketStatus.SUBMITTED.value,
        remarks=f"Ticket submitted via classroom QR code ({location.qr_code_identifier}).",
    )
    db.add(initial_history)
    db.commit()
    db.refresh(ticket)

    return to_ticket_response(ticket)
