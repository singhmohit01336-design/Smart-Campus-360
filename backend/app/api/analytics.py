from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User, UserRole
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import compute_campus_analytics


router = APIRouter(
    prefix="/analytics",
    tags=["Campus Analytics & Reporting"],
    dependencies=[Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN]))],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
)
def get_analytics_summary(
    start_date: datetime | None = Query(default=None, description="Start date for analytics filter"),
    end_date: datetime | None = Query(default=None, description="End date for analytics filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Comprehensive campus-wide analytics and performance indicators.
    Aggregates ticket status, priority, department workload, SLA compliance,
    average resolution time, and daily trends.
    Restricted to Admins and Superadmins.
    """
    return compute_campus_analytics(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
