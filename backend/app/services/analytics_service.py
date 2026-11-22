from datetime import datetime, timezone
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.department import Department
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    CategoryMetric,
    DepartmentMetric,
    PriorityMetric,
    StatusMetric,
    TrendPoint,
)


RESOLVED_STATUSES = [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]


def compute_campus_analytics(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> AnalyticsSummaryResponse:
    """
    Computes aggregated performance metrics and distribution statistics
    using efficient database-level GROUP BY queries.
    """
    now = datetime.now(timezone.utc)

    # Base filter criteria
    base_filters = []
    if start_date:
        base_filters.append(Ticket.created_at >= start_date)
    if end_date:
        base_filters.append(Ticket.created_at <= end_date)

    # 1. Total count
    total_query = select(func.count(Ticket.id))
    if base_filters:
        total_query = total_query.where(*base_filters)
    total_tickets = db.scalar(total_query) or 0

    if total_tickets == 0:
        return AnalyticsSummaryResponse(
            total_tickets=0,
            resolved_tickets=0,
            unresolved_tickets=0,
            resolution_rate_percent=0.0,
            avg_resolution_hours=0.0,
            sla_compliance_rate_percent=100.0,
            overdue_tickets_count=0,
            tickets_by_status=[],
            tickets_by_priority=[],
            tickets_by_department=[],
            tickets_by_category=[],
            ticket_trends_daily=[],
        )

    # 2. Resolved vs Unresolved counts
    resolved_query = select(func.count(Ticket.id)).where(Ticket.status.in_(RESOLVED_STATUSES))
    if base_filters:
        resolved_query = resolved_query.where(*base_filters)
    resolved_tickets = db.scalar(resolved_query) or 0
    unresolved_tickets = total_tickets - resolved_tickets

    resolution_rate = round((resolved_tickets / total_tickets) * 100.0, 2)

    # 3. Average Resolution Time in Hours (SQL Epoch extraction)
    avg_sec_query = select(
        func.avg(func.extract("epoch", Ticket.resolved_at - Ticket.created_at))
    ).where(Ticket.resolved_at.is_not(None))
    if base_filters:
        avg_sec_query = avg_sec_query.where(*base_filters)
    avg_seconds = db.scalar(avg_sec_query)
    avg_resolution_hours = round((avg_seconds / 3600.0), 2) if avg_seconds is not None else 0.0

    # 4. Overdue Tickets Count (Unresolved tickets past SLA deadline)
    overdue_query = select(func.count(Ticket.id)).where(
        ~Ticket.status.in_(RESOLVED_STATUSES),
        Ticket.sla_deadline.is_not(None),
        Ticket.sla_deadline < now,
    )
    if base_filters:
        overdue_query = overdue_query.where(*base_filters)
    overdue_tickets_count = db.scalar(overdue_query) or 0

    # 5. SLA Compliance Percentage
    # Compliant = resolved before/on deadline OR unresolved and not yet overdue
    compliant_condition = case(
        (
            Ticket.status.in_(RESOLVED_STATUSES),
            case((Ticket.resolved_at <= Ticket.sla_deadline, 1), else_=0),
        ),
        else_=case((Ticket.sla_deadline >= now, 1), else_=0),
    )
    compliant_query = select(func.sum(compliant_condition)).where(Ticket.sla_deadline.is_not(None))
    if base_filters:
        compliant_query = compliant_query.where(*base_filters)
    compliant_sum = db.scalar(compliant_query) or 0

    sla_eligible_query = select(func.count(Ticket.id)).where(Ticket.sla_deadline.is_not(None))
    if base_filters:
        sla_eligible_query = sla_eligible_query.where(*base_filters)
    sla_eligible_total = db.scalar(sla_eligible_query) or 0

    sla_compliance_rate = (
        round((compliant_sum / sla_eligible_total) * 100.0, 2)
        if sla_eligible_total > 0
        else 100.0
    )

    # 6. Grouped by Status
    status_query = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    if base_filters:
        status_query = status_query.where(*base_filters)
    status_rows = db.execute(status_query).all()
    tickets_by_status = [StatusMetric(status=row[0], count=row[1]) for row in status_rows]

    # 7. Grouped by Priority
    priority_query = select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
    if base_filters:
        priority_query = priority_query.where(*base_filters)
    priority_rows = db.execute(priority_query).all()
    tickets_by_priority = [PriorityMetric(priority=row[0], count=row[1]) for row in priority_rows]

    # 8. Grouped by Department
    dept_query = (
        select(
            Department.id,
            Department.department_name,
            Department.department_code,
            func.count(Ticket.id),
        )
        .join(Ticket, Ticket.department_id == Department.id)
        .group_by(Department.id, Department.department_name, Department.department_code)
        .order_by(func.count(Ticket.id).desc())
    )
    if base_filters:
        dept_query = dept_query.where(*base_filters)
    dept_rows = db.execute(dept_query).all()
    tickets_by_department = [
        DepartmentMetric(
            department_id=row[0],
            department_name=row[1],
            department_code=row[2],
            count=row[3],
        )
        for row in dept_rows
    ]

    # 9. Grouped by Category
    cat_query = (
        select(
            Category.id,
            Category.category_name,
            Department.department_name,
            func.count(Ticket.id),
        )
        .join(Ticket, Ticket.category_id == Category.id)
        .join(Department, Category.department_id == Department.id)
        .group_by(Category.id, Category.category_name, Department.department_name)
        .order_by(func.count(Ticket.id).desc())
    )
    if base_filters:
        cat_query = cat_query.where(*base_filters)
    cat_rows = db.execute(cat_query).all()
    tickets_by_category = [
        CategoryMetric(
            category_id=row[0],
            category_name=row[1],
            department_name=row[2],
            count=row[3],
        )
        for row in cat_rows
    ]

    # 10. Daily Trends (PostgreSQL to_char for YYYY-MM-DD grouping)
    date_group = func.to_char(Ticket.created_at, "YYYY-MM-DD")
    trend_query = (
        select(date_group.label("day"), func.count(Ticket.id))
        .group_by("day")
        .order_by("day")
    )
    if base_filters:
        trend_query = trend_query.where(*base_filters)
    trend_rows = db.execute(trend_query).all()
    ticket_trends_daily = [TrendPoint(date=row[0], count=row[1]) for row in trend_rows]

    return AnalyticsSummaryResponse(
        total_tickets=total_tickets,
        resolved_tickets=resolved_tickets,
        unresolved_tickets=unresolved_tickets,
        resolution_rate_percent=resolution_rate,
        avg_resolution_hours=avg_resolution_hours,
        sla_compliance_rate_percent=sla_compliance_rate,
        overdue_tickets_count=overdue_tickets_count,
        tickets_by_status=tickets_by_status,
        tickets_by_priority=tickets_by_priority,
        tickets_by_department=tickets_by_department,
        tickets_by_category=tickets_by_category,
        ticket_trends_daily=ticket_trends_daily,
    )
