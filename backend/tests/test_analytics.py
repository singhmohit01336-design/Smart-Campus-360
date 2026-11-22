import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.services.analytics_service import compute_campus_analytics


@pytest.fixture
def analytics_test_context(db_session):
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN.value).first()
    student = db_session.query(User).filter(User.role == UserRole.STUDENT.value).first()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    return {
        "admin": admin,
        "student": student,
        "h_admin": token_for(admin),
        "h_student": token_for(student),
    }


def test_analytics_calculations_and_breakdowns(client, analytics_test_context):
    ctx = analytics_test_context
    response = client.get("/analytics/summary", headers=ctx["h_admin"])
    assert response.status_code == 200
    data = response.json()

    assert "total_tickets" in data
    assert "resolved_tickets" in data
    assert "unresolved_tickets" in data
    assert "resolution_rate_percent" in data
    assert "avg_resolution_hours" in data
    assert "sla_compliance_rate_percent" in data
    assert "overdue_tickets_count" in data
    assert isinstance(data["tickets_by_status"], list)
    assert isinstance(data["tickets_by_priority"], list)
    assert isinstance(data["tickets_by_department"], list)
    assert isinstance(data["tickets_by_category"], list)
    assert isinstance(data["ticket_trends_daily"], list)


def test_analytics_date_filtering(client, analytics_test_context):
    ctx = analytics_test_context
    start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    response = client.get(
        "/analytics/summary",
        params={"start_date": start, "end_date": end},
        headers=ctx["h_admin"],
    )
    assert response.status_code == 200
    assert "total_tickets" in response.json()


def test_unauthorized_analytics_access(client, analytics_test_context):
    ctx = analytics_test_context

    # 1. Student access blocked -> 403 Forbidden
    assert client.get("/analytics/summary", headers=ctx["h_student"]).status_code == 403

    # 2. Unauthenticated access blocked -> 401 Unauthorized
    assert client.get("/analytics/summary").status_code == 401


def test_empty_database_analytics_handling(db_session):
    # Filter with a far-future date window that matches 0 tickets
    far_future = datetime.now(timezone.utc) + timedelta(days=3650)
    result = compute_campus_analytics(db=db_session, start_date=far_future)

    assert result.total_tickets == 0
    assert result.resolved_tickets == 0
    assert result.unresolved_tickets == 0
    assert result.resolution_rate_percent == 0.0
    assert result.avg_resolution_hours == 0.0
    assert result.sla_compliance_rate_percent == 100.0
    assert result.overdue_tickets_count == 0
    assert result.tickets_by_status == []
    assert result.tickets_by_priority == []
    assert result.tickets_by_department == []
    assert result.tickets_by_category == []
    assert result.ticket_trends_daily == []


def test_analytics_with_resolved_tickets_and_decimal_duration(
    client, analytics_test_context, db_session
):
    """
    Regression test for Bug 1:
    PostgreSQL returns Decimal for extract('epoch', ...).
    Verifies that compute_campus_analytics correctly calculates avg_resolution_hours as float
    without throwing TypeError when resolved tickets exist.
    """
    ctx = analytics_test_context
    uid = uuid.uuid4().hex[:6]

    dept = Department(
        department_name=f"Analytics Dept {uid}",
        department_code=f"AN_{uid.upper()}",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    cat = Category(
        category_name=f"Analytics Cat {uid}",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)
    db_session.flush()

    now = datetime.now(timezone.utc)
    t_created = now - timedelta(hours=3, minutes=30)
    t_resolved = now - timedelta(minutes=30)

    ticket = Ticket(
        ticket_number=f"TCK-ANL-{uid}",
        title=f"Resolved ticket for analytics test {uid}",
        description="Testing resolution duration calculation",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=ctx["student"].id,
        location="Lab Test",
        status=TicketStatus.RESOLVED.value,
        priority=TicketPriority.HIGH.value,
        created_at=t_created,
        resolved_at=t_resolved,
        sla_deadline=now + timedelta(hours=10),
    )
    db_session.add(ticket)
    db_session.commit()

    try:
        response = client.get("/analytics/summary", headers=ctx["h_admin"])
        assert response.status_code == 200
        data = response.json()

        assert data["resolved_tickets"] >= 1
        assert data["avg_resolution_hours"] > 0.0
        assert isinstance(data["avg_resolution_hours"], float)
    finally:
        t_obj = db_session.get(Ticket, ticket.id)
        if t_obj:
            db_session.delete(t_obj)
        c_obj = db_session.get(Category, cat.id)
        if c_obj:
            db_session.delete(c_obj)
        d_obj = db_session.get(Department, dept.id)
        if d_obj:
            db_session.delete(d_obj)
        db_session.commit()
