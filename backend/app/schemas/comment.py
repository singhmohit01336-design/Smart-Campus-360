from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)
    is_internal: bool = False


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    comment: str
    is_internal: bool
    created_at: datetime

    author_name: str | None = None
    author_role: str | None = None

    model_config = ConfigDict(from_attributes=True)
