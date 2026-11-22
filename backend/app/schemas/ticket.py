from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category_id: int
    department_id: int
    location: str = Field(min_length=2, max_length=200)
    building: str | None = Field(default=None, max_length=100)
    room_number: str | None = Field(default=None, max_length=50)
    qr_code_identifier: str | None = Field(default=None, max_length=100)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketAssignRequest(BaseModel):
    technician_id: int


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus
    remarks: str | None = Field(default=None, max_length=1000)


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    category_id: int
    department_id: int
    created_by_id: int
    assigned_to_id: int | None = None
    location: str
    building: str | None = None
    room_number: str | None = None
    qr_code_identifier: str | None = None
    priority: str
    status: str
    sla_deadline: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Denormalized presentation metadata
    creator_name: str | None = None
    creator_email: str | None = None
    assignee_name: str | None = None
    category_name: str | None = None
    department_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedTicketsResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
