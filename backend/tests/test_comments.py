import uuid
import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.ticket import Ticket
from app.models.user import User, UserRole


@pytest.fixture
def comment_test_context(db_session):
    uid = uuid.uuid4().hex[:6]

    dept = Department(
        department_name=f"Comment Test Dept {uid}",
        department_code=f"CD_{uid.upper()}",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    cat = Category(
        category_name=f"Comment Test Cat {uid}",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)

    student = User(
        full_name=f"Student Commenter {uid}",
        email=f"comment_student_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    other_student = User(
        full_name=f"Other Student {uid}",
        email=f"other_student_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    faculty = User(
        full_name=f"Faculty Professor {uid}",
        email=f"comment_faculty_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.FACULTY.value,
        is_active=True,
    )
    technician = User(
        full_name=f"Technician Responder {uid}",
        email=f"comment_tech_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.TECHNICIAN.value,
        is_active=True,
    )
    admin = User(
        full_name=f"Admin Supervisor {uid}",
        email=f"comment_admin_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add_all([student, other_student, faculty, technician, admin])
    db_session.commit()

    ticket = Ticket(
        ticket_number=f"TCK-CMT-{uid}",
        title="Microphone not working in Seminar Hall",
        description="Wireless lapel mic has continuous static and low output volume.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        assigned_to_id=technician.id,
        location="Seminar Hall 1",
    )
    db_session.add(ticket)
    db_session.commit()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    ctx = {
        "dept": dept,
        "cat": cat,
        "student": student,
        "other_student": other_student,
        "faculty": faculty,
        "technician": technician,
        "admin": admin,
        "ticket": ticket,
        "h_student": token_for(student),
        "h_other_student": token_for(other_student),
        "h_faculty": token_for(faculty),
        "h_tech": token_for(technician),
        "h_admin": token_for(admin),
    }
    yield ctx

    # Cleanup
    db_session.rollback()
    t = db_session.get(Ticket, ticket.id)
    if t:
        db_session.delete(t)
    db_session.commit()

    for u in [student, other_student, faculty, technician, admin]:
        user_obj = db_session.get(User, u.id)
        if user_obj:
            db_session.delete(user_obj)
    cat_obj = db_session.get(Category, cat.id)
    if cat_obj:
        db_session.delete(cat_obj)
    dept_obj = db_session.get(Department, dept.id)
    if dept_obj:
        db_session.delete(dept_obj)
    db_session.commit()


def test_public_and_internal_comment_posting(client, comment_test_context):
    ctx = comment_test_context
    t_id = ctx["ticket"].id

    # 1. Student posts public comment -> 201
    resp1 = client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "We need this by 3:00 PM for guest lecture.", "is_internal": False},
        headers=ctx["h_student"],
    )
    assert resp1.status_code == 201
    assert resp1.json()["is_internal"] is False
    assert resp1.json()["author_name"] == ctx["student"].full_name

    # 2. Student attempts to post internal note -> 403 Forbidden
    resp_hack = client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Hacking internal note", "is_internal": True},
        headers=ctx["h_student"],
    )
    assert resp_hack.status_code == 403
    assert "internal staff notes" in resp_hack.json()["detail"]

    # 3. Technician posts internal note -> 201
    resp2 = client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Batteries replaced, receiver antenna checked.", "is_internal": True},
        headers=ctx["h_tech"],
    )
    assert resp2.status_code == 201
    assert resp2.json()["is_internal"] is True

    # 4. Admin posts internal note -> 201
    resp3 = client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Noted by supervisor, spare transmitter ready.", "is_internal": True},
        headers=ctx["h_admin"],
    )
    assert resp3.status_code == 201


def test_internal_notes_visibility_filtered_for_students(client, comment_test_context):
    ctx = comment_test_context
    t_id = ctx["ticket"].id

    # Post 1 public comment and 1 internal note
    client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Public update: technician dispatched.", "is_internal": False},
        headers=ctx["h_tech"],
    )
    client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Internal note: audio mixer channel 4 gain potentiometer is scratchy.", "is_internal": True},
        headers=ctx["h_tech"],
    )

    # 1. Student queries comments -> must NOT see the internal note
    student_comments = client.get(f"/tickets/{t_id}/comments/", headers=ctx["h_student"]).json()
    assert len(student_comments) == 1
    assert student_comments[0]["is_internal"] is False
    assert "Public update" in student_comments[0]["comment"]

    # 2. Technician queries comments -> must see BOTH comments
    tech_comments = client.get(f"/tickets/{t_id}/comments/", headers=ctx["h_tech"]).json()
    assert len(tech_comments) == 2
    assert any(c["is_internal"] is True for c in tech_comments)
    assert any(c["is_internal"] is False for c in tech_comments)


def test_unauthorized_user_cannot_access_comments(client, comment_test_context):
    ctx = comment_test_context
    t_id = ctx["ticket"].id

    # Unrelated student attempts to read or post comments -> 403 Forbidden
    assert client.get(f"/tickets/{t_id}/comments/", headers=ctx["h_other_student"]).status_code == 403
    assert client.post(
        f"/tickets/{t_id}/comments/",
        json={"comment": "Unauthorized comment"},
        headers=ctx["h_other_student"],
    ).status_code == 403


def test_faculty_internal_notes_isolation(client, comment_test_context, db_session):
    """
    Security verification:
    1. Faculty member cannot create internal notes (must return 403 Forbidden).
    2. Faculty member who created a ticket cannot view internal notes added by technicians/admins.
    """
    ctx = comment_test_context
    uid = uuid.uuid4().hex[:6]

    # Create a ticket authored by the faculty member
    faculty_ticket = Ticket(
        ticket_number=f"TCK-FAC-{uid}",
        title="Projector bulb replacement in CS Lab 3",
        description="Bulb is flickering during lectures.",
        category_id=ctx["cat"].id,
        department_id=ctx["dept"].id,
        created_by_id=ctx["faculty"].id,
        assigned_to_id=ctx["technician"].id,
        location="CS Lab 3",
    )
    db_session.add(faculty_ticket)
    db_session.commit()

    try:
        # 1. Faculty member attempts to post an internal note -> 403 Forbidden
        resp_post = client.post(
            f"/tickets/{faculty_ticket.id}/comments/",
            json={"comment": "Attempting to post internal faculty note", "is_internal": True},
            headers=ctx["h_faculty"],
        )
        assert resp_post.status_code == 403
        assert "internal staff notes" in resp_post.json()["detail"].lower()

        # 2. Faculty member posts a public comment -> 201 Created
        resp_pub = client.post(
            f"/tickets/{faculty_ticket.id}/comments/",
            json={"comment": "Class starts at 10 AM tomorrow.", "is_internal": False},
            headers=ctx["h_faculty"],
        )
        assert resp_pub.status_code == 201
        assert resp_pub.json()["is_internal"] is False

        # 3. Technician posts an internal staff note -> 201 Created
        resp_tech_internal = client.post(
            f"/tickets/{faculty_ticket.id}/comments/",
            json={"comment": "Spare bulb ordered from vendor inventory.", "is_internal": True},
            headers=ctx["h_tech"],
        )
        assert resp_tech_internal.status_code == 201

        # 4. Faculty fetches comments on their ticket -> must NOT see the technician's internal note
        resp_get = client.get(
            f"/tickets/{faculty_ticket.id}/comments/",
            headers=ctx["h_faculty"],
        )
        assert resp_get.status_code == 200
        comments = resp_get.json()
        assert len(comments) == 1
        assert comments[0]["is_internal"] is False
        assert "Class starts at 10 AM tomorrow." in comments[0]["comment"]
        assert not any(c.get("is_internal") is True for c in comments)
        assert not any("Spare bulb" in c.get("comment", "") for c in comments)

        # 5. Technician and Admin fetch comments -> CAN see internal note
        resp_tech_get = client.get(
            f"/tickets/{faculty_ticket.id}/comments/",
            headers=ctx["h_tech"],
        )
        assert resp_tech_get.status_code == 200
        tech_comments = resp_tech_get.json()
        assert len(tech_comments) == 2
        assert any(c.get("is_internal") is True for c in tech_comments)
    finally:
        t = db_session.get(Ticket, faculty_ticket.id)
        if t:
            db_session.delete(t)
        db_session.commit()
