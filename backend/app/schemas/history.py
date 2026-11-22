from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HistoryResponse(BaseModel):
    id: int
    ticket_id: int
    changed_by_id: int
    old_status: str | None = None
    new_status: str
    remarks: str | None = None
    created_at: datetime

    changed_by_name: str | None = None
    changed_by_role: str | None = None

    model_config = ConfigDict(from_attributes=True)
