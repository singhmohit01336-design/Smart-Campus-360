import uuid
import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole


@pytest.fixture
def ticket_test_context(db_session):
    """Fixture providing isolated users, department, and category for ticket testing."""
    uid = uuid.uuid4().hex[:6]

    dept = Department(
        department_name=f"Campus Tech Dept {uid}",
        department_code=f"CT_{uid.upper()}",
        description="Department for ticket tests",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    cat = Category(
        category_name=f"Hardware Issues {uid}",
        description="Hardware faults",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)

    student_a = User(
        full_name=f"Student A {uid}",
        email=f"student_a_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    faculty_b = User(
        full_name=f"Faculty B {uid}",
        email=f"faculty_b_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.FACULTY.value,
        is_active=True,
    )
    technician_c = User(
        full_name=f"Technician C {uid}",
        email=f"tech_c_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.TECHNICIAN.value,
        is_active=True,
    )
    admin_d = User(
        full_name=f"Admin D {uid}",
        email=f"admin_d_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    inactive_tech = User(
        full_name=f"Inactive Tech {uid}",
        email=f"inactive_tech_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.TECHNICIAN.value,
        is_active=False,
    )
    db_session.add_all([student_a, faculty_b, technician_c, admin_d, inactive_tech])
    db_session.commit()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    ctx = {
        "dept": dept,
        "cat": cat,
        "student_a": student_a,
        "faculty_b": faculty_b,
        "technician_c": technician_c,
        "admin_d": admin_d,
        "inactive_tech": inactive_tech,
        "h_student_a": token_for(student_a),
        "h_faculty_b": token_for(faculty_b),
        "h_tech_c": token_for(technician_c),
        "h_admin_d": token_for(admin_d),
        "uid": uid,
    }
    yield ctx

    # Cleanup
    db_session.rollback()
    tickets = db_session.scalars(select(Ticket).where(Ticket.department_id == dept.id)).all()
    for t in tickets:
        db_session.delete(t)
    db_session.commit()

    for u in [student_a, faculty_b, technician_c, admin_d, inactive_tech]:
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


def test_ticket_creation_and_sla_deadlines(client, ticket_test_context):
    ctx = ticket_test_context
    headers = ctx["h_student_a"]

    # 1. Student creates normal ticket (Medium priority -> 24h SLA)
    payload_medium = {
        "title": "Classroom ceiling fan speed regulator broken",
        "description": "Fan is stuck on maximum speed and making loud vibrations.",
        "category_id": ctx["cat"].id,
        "department_id": ctx["dept"].id,
        "location": "Main Campus Building 2, Room 204",
        "building": "Building 2",
        "room_number": "204",
        "qr_code_identifier": f"QR-B2-204-{ctx['uid']}",
        "priority": "medium",
    }
    resp1 = client.post("/tickets/", json=payload_medium, headers=headers)
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["ticket_number"].startswith("TCK-")
    assert data1["status"] == "submitted"
    assert data1["created_by_id"] == ctx["student_a"].id
    assert data1["sla_deadline"] is not None

    # 2. Faculty creates Critical priority ticket -> 4h SLA
    payload_critical = {
        "title": "Server rack temperature alert in Lab 3",
        "description": "AC unit failed, rack temp exceeds 38 degrees Celsius.",
        "category_id": ctx["cat"].id,
        "department_id": ctx["dept"].id,
        "location": "Server Lab 3",
        "priority": "critical",
    }
    resp2 = client.post("/tickets/", json=payload_critical, headers=ctx["h_faculty_b"])
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["priority"] == "critical"
    assert data2["ticket_number"] != data1["ticket_number"]


def test_ticket_creation_validation(client, ticket_test_context):
    ctx = ticket_test_context
    headers = ctx["h_student_a"]

    # Nonexistent department
    bad_dept = {
        "title": "Valid title here",
        "description": "Valid description explaining the issue in detail.",
        "category_id": ctx["cat"].id,
        "department_id": 999999,
        "location": "Room 101",
    }
    assert client.post("/tickets/", json=bad_dept, headers=headers).status_code == 400

    # Description too short (< 10 chars)
    short_desc = {
        "title": "Valid title",
        "description": "Short",
        "category_id": ctx["cat"].id,
        "department_id": ctx["dept"].id,
        "location": "Room 101",
    }
    assert client.post("/tickets/", json=short_desc, headers=headers).status_code == 422


def test_role_based_ticket_listing_visibility(client, ticket_test_context):
    ctx = ticket_test_context

    # Student A creates Ticket 1
    t1_resp = client.post(
        "/tickets/",
        json={
            "title": "Student A Ticket - Network Port 12",
            "description": "Ethernet wall jack is loose and disconnects constantly.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Library Desk 12",
        },
        headers=ctx["h_student_a"],
    )
    assert t1_resp.status_code == 201
    t1_id = t1_resp.json()["id"]

    # Faculty B creates Ticket 2
    t2_resp = client.post(
        "/tickets/",
        json={
            "title": "Faculty B Ticket - Smart Board Pen",
            "description": "Interactive stylus is missing from podium.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Auditorium 1",
        },
        headers=ctx["h_faculty_b"],
    )
    assert t2_resp.status_code == 201
    t2_id = t2_resp.json()["id"]

    # Admin assigns Ticket 1 to Technician C
    assign_resp = client.patch(
        f"/tickets/{t1_id}/assign",
        json={"technician_id": ctx["technician_c"].id},
        headers=ctx["h_admin_d"],
    )
    assert assign_resp.status_code == 200

    # 1. Student A listing: must ONLY see Ticket 1
    s_list = client.get("/tickets/", headers=ctx["h_student_a"]).json()["items"]
    s_ids = [t["id"] for t in s_list]
    assert t1_id in s_ids
    assert t2_id not in s_ids

    # 2. Faculty B listing: must ONLY see Ticket 2
    f_list = client.get("/tickets/", headers=ctx["h_faculty_b"]).json()["items"]
    f_ids = [t["id"] for t in f_list]
    assert t2_id in f_ids
    assert t1_id not in f_ids

    # 3. Technician C listing: must see assigned Ticket 1, but NOT Ticket 2
    tech_list = client.get("/tickets/", headers=ctx["h_tech_c"]).json()["items"]
    tech_ids = [t["id"] for t in tech_list]
    assert t1_id in tech_ids
    assert t2_id not in tech_ids

    # 4. Admin listing: must see BOTH Ticket 1 and Ticket 2
    admin_list = client.get("/tickets/", headers=ctx["h_admin_d"]).json()["items"]
    admin_ids = [t["id"] for t in admin_list]
    assert t1_id in admin_ids
    assert t2_id in admin_ids


def test_ticket_search_and_filtering(client, ticket_test_context):
    ctx = ticket_test_context

    # Create distinct tickets
    client.post(
        "/tickets/",
        json={
            "title": "Water cooler leaking in hallway",
            "description": "Continuous leak creating slippery hazard near stairs.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Corridor West",
            "priority": "high",
        },
        headers=ctx["h_student_a"],
    )

    # Search by keyword
    search_resp = client.get("/tickets/?search=cooler", headers=ctx["h_student_a"])
    assert search_resp.status_code == 200
    items = search_resp.json()["items"]
    assert len(items) >= 1
    assert "cooler" in items[0]["title"].lower()

    # Filter by priority
    filter_high = client.get("/tickets/?priority=high", headers=ctx["h_student_a"]).json()["items"]
    assert all(t["priority"] == "high" for t in filter_high)


def test_ticket_details_authorization(client, ticket_test_context):
    ctx = ticket_test_context

    # Student A ticket
    t_resp = client.post(
        "/tickets/",
        json={
            "title": "Printer paper jam in department office",
            "description": "Paper tray 2 is stuck with torn sheets.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Admin Office",
        },
        headers=ctx["h_student_a"],
    )
    ticket_id = t_resp.json()["id"]

    # Student A can view
    assert client.get(f"/tickets/{ticket_id}", headers=ctx["h_student_a"]).status_code == 200

    # Faculty B (unauthorized third party) cannot view -> 403
    assert client.get(f"/tickets/{ticket_id}", headers=ctx["h_faculty_b"]).status_code == 403

    # Admin can view
    assert client.get(f"/tickets/{ticket_id}", headers=ctx["h_admin_d"]).status_code == 200


def test_ticket_assignment_restrictions(client, ticket_test_context):
    ctx = ticket_test_context

    t_resp = client.post(
        "/tickets/",
        json={
            "title": "Broken window latch in room 401",
            "description": "Window cannot be securely latched during rain.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Room 401",
        },
        headers=ctx["h_student_a"],
    )
    ticket_id = t_resp.json()["id"]

    # Non-admin student cannot assign -> 403
    assert client.patch(
        f"/tickets/{ticket_id}/assign",
        json={"technician_id": ctx["technician_c"].id},
        headers=ctx["h_student_a"],
    ).status_code == 403

    # Admin cannot assign to a student (not a technician) -> 400
    bad_assign = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={"technician_id": ctx["student_a"].id},
        headers=ctx["h_admin_d"],
    )
    assert bad_assign.status_code == 400
    assert "not a technician" in bad_assign.json()["detail"]

    # Admin cannot assign to inactive technician -> 400
    inactive_assign = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={"technician_id": ctx["inactive_tech"].id},
        headers=ctx["h_admin_d"],
    )
    assert inactive_assign.status_code == 400
    assert "inactive" in inactive_assign.json()["detail"]

    # Valid assignment to technician C -> 200
    valid_assign = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={"technician_id": ctx["technician_c"].id},
        headers=ctx["h_admin_d"],
    )
    assert valid_assign.status_code == 200
    assert valid_assign.json()["assigned_to_id"] == ctx["technician_c"].id
    assert valid_assign.json()["status"] == "assigned"


def test_ticket_status_workflow_transitions(client, ticket_test_context):
    ctx = ticket_test_context

    t_resp = client.post(
        "/tickets/",
        json={
            "title": "Lab 5 Projector Bulb Replacement",
            "description": "Projector bulb burned out during presentation.",
            "category_id": ctx["cat"].id,
            "department_id": ctx["dept"].id,
            "location": "Lab 5",
        },
        headers=ctx["h_student_a"],
    )
    ticket_id = t_resp.json()["id"]

    # Assign to technician
    client.patch(
        f"/tickets/{ticket_id}/assign",
        json={"technician_id": ctx["technician_c"].id},
        headers=ctx["h_admin_d"],
    )

    # 1. Technician marks in_progress
    resp_ip = client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "in_progress", "remarks": "Replaced bulb, testing display."},
        headers=ctx["h_tech_c"],
    )
    assert resp_ip.status_code == 200
    assert resp_ip.json()["status"] == "in_progress"

    # 2. Technician marks resolved -> resolved_at must be populated
    resp_res = client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "resolved", "remarks": "Display calibrated and operational."},
        headers=ctx["h_tech_c"],
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "resolved"
    assert resp_res.json()["resolved_at"] is not None

    # 3. Technician cannot close the ticket -> 400
    assert client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "closed"},
        headers=ctx["h_tech_c"],
    ).status_code == 400

    # 4. Student creator accepts and closes ticket -> 200
    resp_close = client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "closed", "remarks": "Verified working. Thank you!"},
        headers=ctx["h_student_a"],
    )
    assert resp_close.status_code == 200
    assert resp_close.json()["status"] == "closed"

    # 5. Student reopens closed ticket -> 200
    resp_reopen = client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "reopened", "remarks": "Flickering issue returned."},
        headers=ctx["h_student_a"],
    )
    assert resp_reopen.status_code == 200
    assert resp_reopen.json()["status"] == "reopened"
    assert resp_reopen.json()["resolved_at"] is None

    # Check History Audit
    hist_resp = client.get(f"/tickets/{ticket_id}/history", headers=ctx["h_student_a"])
    assert hist_resp.status_code == 200
    history_entries = hist_resp.json()
    assert len(history_entries) >= 5
