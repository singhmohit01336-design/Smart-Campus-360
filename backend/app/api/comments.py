from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.comment import TicketComment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.ticket_service import check_ticket_access


router = APIRouter(
    prefix="/tickets/{ticket_id}/comments",
    tags=["Ticket Comments"],
)


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a comment or internal work note to a ticket.
    - Public comments can be posted by any user with ticket access.
    - Internal notes (is_internal=True) are strictly restricted to staff (Technicians, Admins, Superadmins).
    """
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else str(current_user.role).lower()
    )

    # Restrict internal note creation to authorized staff
    if payload.is_internal and user_role in {UserRole.STUDENT.value, UserRole.FACULTY.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students and faculty cannot post internal staff notes.",
        )

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        comment=payload.comment.strip(),
        is_internal=payload.is_internal,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        ticket_id=comment.ticket_id,
        user_id=comment.user_id,
        comment=comment.comment,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
        author_name=current_user.full_name,
        author_role=current_user.role,
    )


@router.get(
    "/",
    response_model=list[CommentResponse],
)
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List chronological comments for a ticket.
    - Students and faculty only see public comments (internal notes are strictly filtered out).
    - Authorized staff (technicians, admins, superadmins) see both public and internal notes.
    """
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else str(current_user.role).lower()
    )

    query = (
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc())
    )

    # Non-staff users must NEVER see internal notes
    if user_role in {UserRole.STUDENT.value, UserRole.FACULTY.value}:
        query = query.where(TicketComment.is_internal == False)

    comments = db.scalars(query).all()

    return [
        CommentResponse(
            id=c.id,
            ticket_id=c.ticket_id,
            user_id=c.user_id,
            comment=c.comment,
            is_internal=c.is_internal,
            created_at=c.created_at,
            author_name=c.user.full_name if c.user else None,
            author_role=c.user.role if c.user else None,
        )
        for c in comments
    ]
