import os
from pathlib import Path
import time
import uuid
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes


def validate_file_magic_bytes(header: bytes, ext: str) -> bool:
    """Validate initial file signatures (magic bytes) against expected formats."""
    if ext == ".pdf":
        return header.startswith(b"%PDF")
    if ext in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    return False


async def save_uploaded_file(file: UploadFile) -> dict:
    """
    Validates uploaded file extension, MIME type, magic bytes, and file size.
    Saves file to local upload directory using an unguessable unique stored filename.
    Returns metadata dictionary for database persistence.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # 1. Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: PDF, JPG, JPEG, PNG.",
        )

    # 2. Validate MIME type
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file MIME type '{content_type}'.",
        )

    # 3. Read content and validate size & magic bytes
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 5 MB ({file_size} bytes uploaded).",
        )

    if not validate_file_magic_bytes(content[:16], ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content header does not match expected format signature.",
        )

    # 4. Generate collision-resistant unique filename
    unique_id = uuid.uuid4().hex[:12]
    timestamp = int(time.time())
    stored_filename = f"att_{unique_id}_{timestamp}{ext}"

    # Ensure upload directory exists
    target_dir = settings.upload_path / "tickets"
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / stored_filename

    # Save to disk
    with open(destination, "wb") as f:
        f.write(content)

    return {
        "original_filename": Path(file.filename).name,
        "stored_filename": stored_filename,
        "file_type": content_type,
        "file_size": file_size,
        "storage_path": str(destination.relative_to(settings.upload_path.parent)),
    }
