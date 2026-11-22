from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    uploaded_by_id: int
    original_filename: str
    file_type: str
    file_size: int
    created_at: datetime

    uploader_name: str | None = None
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
