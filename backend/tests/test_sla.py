from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.notification import Notification
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole


@pytest.fixture
def sla_test_context(db_session):
    uid = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)

    dept = Department(
        department_name=f"SLA Dept {uid}",
        department_code=f"SD_{uid.upper()}",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    cat = Category(
        category_name=f"SLA Category {uid}",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)

    admin = User(
        full_name=f"SLA Admin {uid}",
        email=f"sla_admin_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    student = User(
        full_name=f"SLA Student {uid}",
        email=f"sla_student_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    technician = User(
        full_name=f"SLA Tech {uid}",
        email=f"sla_tech_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.TECHNICIAN.value,
        is_active=True,
    )
    db_session.add_all([admin, student, technician])
    db_session.commit()

    # Ticket 1: Overdue ticket (deadline was 3 hours ago)
    t_overdue = Ticket(
        ticket_number=f"TCK-SLA-OVD-{uid}",
        title="Overdue server outage",
        description="Core switch power supply failure.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        assigned_to_id=technician.id,
        location="Server Room 1",
        status=TicketStatus.IN_PROGRESS.value,
        priority=TicketPriority.CRITICAL.value,
        sla_deadline=now - timedelta(hours=3),
    )
    # Ticket 2: Approaching deadline (due in 1 hour)
    t_approaching = Ticket(
        ticket_number=f"TCK-SLA-APP-{uid}",
        title="Approaching deadline lab fault",
        description="Air conditioner failure in workstation lab.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        assigned_to_id=technician.id,
        location="Lab 202",
        status=TicketStatus.ASSIGNED.value,
        priority=TicketPriority.HIGH.value,
        sla_deadline=now + timedelta(hours=1),
    )
    # Ticket 3: On-time ticket (due in 48 hours)
    t_ontime = Ticket(
        ticket_number=f"TCK-SLA-ONT-{uid}",
        title="Routine desk repair",
        description="Loose hinge on teacher desk.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Room 105",
        status=TicketStatus.SUBMITTED.value,
        priority=TicketPriority.LOW.value,
        sla_deadline=now + timedelta(hours=48),
    )
    db_session.add_all([t_overdue, t_approaching, t_ontime])
    db_session.commit()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    ctx = {
        "admin": admin,
        "student": student,
        "technician": technician,
        "h_admin": token_for(admin),
        "h_student": token_for(student),
        "t_overdue": t_overdue,
        "t_approaching": t_approaching,
        "t_ontime": t_ontime,
    }
    yield ctx

    # Cleanup
    db_session.rollback()
    for t in [t_overdue, t_approaching, t_ontime]:
        t_obj = db_session.get(Ticket, t.id)
        if t_obj:
            db_session.delete(t_obj)
    db_session.commit()

    # Clean notifications
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.user_id.in_([admin.id, student.id, technician.id])
        )
    ).all()
    for n in notifs:
        db_session.delete(n)

    for u in [admin, student, technician]:
        u_obj = db_session.get(User, u.id)
        if u_obj:
            db_session.delete(u_obj)
    cat_obj = db_session.get(Category, cat.id)
    if cat_obj:
        db_session.delete(cat_obj)
    dept_obj = db_session.get(Department, dept.id)
    if dept_obj:
        db_session.delete(dept_obj)
    db_session.commit()


def test_sla_stats_and_overdue_endpoints(client, sla_test_context):
    ctx = sla_test_context

    # 1. Get SLA statistics
    stats_resp = client.get("/sla/stats", headers=ctx["h_admin"])
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_active_tickets"] >= 3
    assert stats["overdue_tickets"] >= 1
    assert stats["approaching_deadline_tickets"] >= 1
    assert stats["sla_compliance_rate"] <= 100.0

    # 2. Get list of overdue tickets
    overdue_resp = client.get("/sla/overdue", headers=ctx["h_admin"])
    assert overdue_resp.status_code == 200
    overdue_list = overdue_resp.json()
    overdue_numbers = [t["ticket_number"] for t in overdue_list]
    assert ctx["t_overdue"].ticket_number in overdue_numbers
    assert ctx["t_ontime"].ticket_number not in overdue_numbers


def test_sla_check_notification_and_duplicate_prevention(client, sla_test_context):
    ctx = sla_test_context

    # 1. Trigger SLA check manually
    check_resp1 = client.post("/sla/check", headers=ctx["h_admin"])
    assert check_resp1.status_code == 200
    res1 = check_resp1.json()
    assert res1["overdue_detected"] >= 1
    assert res1["approaching_detected"] >= 1
    assert res1["notifications_created"] >= 1

    # 2. Trigger SLA check a second time -> Must skip duplicate alerts!
    check_resp2 = client.post("/sla/check", headers=ctx["h_admin"])
    assert check_resp2.status_code == 200
    res2 = check_resp2.json()
    assert res2["notifications_created"] == 0  # Zero duplicate notifications created!
    assert res2["notifications_skipped_duplicate"] >= 1


def test_sla_endpoints_role_guard(client, sla_test_context):
    ctx = sla_test_context

    # Student cannot access admin-only SLA management endpoints -> 403 Forbidden
    assert client.get("/sla/stats", headers=ctx["h_student"]).status_code == 403
    assert client.get("/sla/overdue", headers=ctx["h_student"]).status_code == 403
    assert client.post("/sla/check", headers=ctx["h_student"]).status_code == 403
