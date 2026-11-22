from pydantic import BaseModel


class SLAStatsResponse(BaseModel):
    total_active_tickets: int
    on_time_tickets: int
    approaching_deadline_tickets: int
    overdue_tickets: int
    sla_compliance_rate: float


class SLACheckResultResponse(BaseModel):
    evaluated_tickets: int
    overdue_detected: int
    approaching_detected: int
    notifications_created: int
    notifications_skipped_duplicate: int
