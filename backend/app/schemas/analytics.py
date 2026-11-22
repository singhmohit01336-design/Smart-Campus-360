from pydantic import BaseModel


class StatusMetric(BaseModel):
    status: str
    count: int


class PriorityMetric(BaseModel):
    priority: str
    count: int


class DepartmentMetric(BaseModel):
    department_id: int
    department_name: str
    department_code: str
    count: int


class CategoryMetric(BaseModel):
    category_id: int
    category_name: str
    department_name: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    total_tickets: int
    resolved_tickets: int
    unresolved_tickets: int
    resolution_rate_percent: float
    avg_resolution_hours: float
    sla_compliance_rate_percent: float
    overdue_tickets_count: int
    tickets_by_status: list[StatusMetric]
    tickets_by_priority: list[PriorityMetric]
    tickets_by_department: list[DepartmentMetric]
    tickets_by_category: list[CategoryMetric]
    ticket_trends_daily: list[TrendPoint]
