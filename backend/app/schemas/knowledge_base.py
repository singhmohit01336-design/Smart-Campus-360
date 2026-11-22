from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=10)
    category_id: int | None = None
    is_published: bool = True


class KnowledgeBaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    content: str | None = Field(default=None, min_length=10)
    category_id: int | None = None
    is_published: bool | None = None


class KnowledgeBasePublishRequest(BaseModel):
    is_published: bool


class KnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    content: str
    category_id: int | None = None
    category_name: str | None = None
    created_by_id: int
    author_name: str | None = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedKnowledgeBaseResponse(BaseModel):
    items: list[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
