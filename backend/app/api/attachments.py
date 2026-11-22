from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.attachment import Attachment
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.attachment import AttachmentResponse
from app.services.attachment_service import save_uploaded_file
from app.services.ticket_service import check_ticket_access


router = APIRouter(
    prefix="/tickets/{ticket_id}/attachments",
    tags=["Ticket Attachments"],
)


@router.post(
    "/",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(..., description="Attachment file (PDF, JPG, JPEG, PNG up to 5 MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a secure attachment for an existing ticket.
    Validates file extension, MIME type, magic bytes, and file size.
    Saves file to server storage with an unguessable unique filename.
    """
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    # Process and save file safely
    file_metadata = await save_uploaded_file(file)

    attachment = Attachment(
        ticket_id=ticket.id,
        uploaded_by_id=current_user.id,
        original_filename=file_metadata["original_filename"],
        stored_filename=file_metadata["stored_filename"],
        file_type=file_metadata["file_type"],
        file_size=file_metadata["file_size"],
        storage_path=file_metadata["storage_path"],
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return AttachmentResponse(
        id=attachment.id,
        ticket_id=attachment.ticket_id,
        uploaded_by_id=attachment.uploaded_by_id,
        original_filename=attachment.original_filename,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        created_at=attachment.created_at,
        uploader_name=current_user.full_name,
        download_url=f"/tickets/{ticket.id}/attachments/{attachment.id}/download",
    )


@router.get(
    "/",
    response_model=list[AttachmentResponse],
)
def list_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List metadata for all files attached to a ticket.
    Filesystem paths are never exposed to clients.
    """
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.ticket_id == ticket_id)
        .order_by(Attachment.created_at.asc())
    ).all()

    return [
        AttachmentResponse(
            id=att.id,
            ticket_id=att.ticket_id,
            uploaded_by_id=att.uploaded_by_id,
            original_filename=att.original_filename,
            file_type=att.file_type,
            file_size=att.file_size,
            created_at=att.created_at,
            uploader_name=att.uploaded_by.full_name if att.uploaded_by else None,
            download_url=f"/tickets/{ticket.id}/attachments/{att.id}/download",
        )
        for att in attachments
    ]


@router.get(
    "/{attachment_id}/download",
)
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Securely download an attachment file.
    Validates ticket stakeholder authorization and serves file stream.
    """
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    check_ticket_access(ticket, current_user)

    attachment = db.scalar(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.ticket_id == ticket_id,
        )
    )
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found.",
        )

    file_path = settings.upload_path / "tickets" / attachment.stored_filename
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file could not be found on storage.",
        )

    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.file_type,
    )
