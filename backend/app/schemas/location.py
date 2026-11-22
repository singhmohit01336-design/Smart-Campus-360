from pydantic import BaseModel, ConfigDict, Field
from app.models.ticket import TicketPriority


class CampusLocationResponse(BaseModel):
    id: int
    qr_code_identifier: str
    building: str
    room_number: str
    floor: str | None = None
    location_name: str
    department_id: int | None = None
    department_name: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class QRTicketCreate(BaseModel):
    qr_code_identifier: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category_id: int
    department_id: int | None = None
    priority: TicketPriority = TicketPriority.MEDIUM
