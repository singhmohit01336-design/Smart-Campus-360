from pydantic import BaseModel, Field


class CategorySuggestionRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=2000)


class CategorySuggestionResponse(BaseModel):
    suggested_department_id: int | None = None
    suggested_department_name: str | None = None
    suggested_category_id: int | None = None
    suggested_category_name: str | None = None
    confidence_score: float
    confidence_level: str  # "high", "medium", "low"
    matched_keywords: list[str] = []
    is_fallback: bool = False


class PrioritySuggestionRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=2000)


class PrioritySuggestionResponse(BaseModel):
    suggested_priority: str
    reason: str
    urgency_factors: list[str] = []
