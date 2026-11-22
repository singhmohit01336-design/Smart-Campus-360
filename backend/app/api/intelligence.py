from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.intelligence import (
    CategorySuggestionRequest,
    CategorySuggestionResponse,
    PrioritySuggestionRequest,
    PrioritySuggestionResponse,
)
from app.services.intelligence_service import (
    suggest_category_and_department,
    suggest_ticket_priority,
)


router = APIRouter(
    prefix="/intelligence",
    tags=["Campus Intelligence & AI Rules"],
)


@router.post(
    "/suggest-category",
    response_model=CategorySuggestionResponse,
)
def get_category_suggestion(
    payload: CategorySuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Suggests the most appropriate department and category based on rule-based text analysis.
    Returns confidence score and keywords to assist students and faculty during ticket drafting.
    """
    return suggest_category_and_department(
        title=payload.title,
        description=payload.description,
        db=db,
    )


@router.post(
    "/suggest-priority",
    response_model=PrioritySuggestionResponse,
)
def get_priority_suggestion(
    payload: PrioritySuggestionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Suggests ticket priority (Critical, High, Medium, Low) based on safety risks and disruption impact.
    Returns clear human-readable justification.
    """
    return suggest_ticket_priority(
        title=payload.title,
        description=payload.description,
    )
