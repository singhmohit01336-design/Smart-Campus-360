from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.comment import TicketComment
from app.models.history import TicketHistory
from app.models.attachment import Attachment
from app.models.notification import Notification
from app.models.knowledge_base import KnowledgeBase


@pytest.fixture
def test_setup_entities(db_session):
    """
    Creates isolated test entities (Department, Category, Student, Technician, Admin)
    for model relationship and constraint verification.
    """
    uid = uuid.uuid4().hex[:8]

    # 1. Department
    dept = Department(
        department_name=f"Test Dept {uid}",
        department_code=f"TD_{uid[:4].upper()}",
        description="Isolated test department",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    # 2. Category
    cat = Category(
        category_name=f"Test Category {uid}",
        description="Category for testing",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)

    # 3. Users
    student = User(
        full_name=f"Test Student {uid}",
        email=f"student_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        department_id=dept.id,
    )
    technician = User(
        full_name=f"Test Tech {uid}",
        email=f"tech_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.TECHNICIAN.value,
        department_id=dept.id,
    )
    admin = User(
        full_name=f"Test Admin {uid}",
        email=f"admin_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.ADMIN.value,
        department_id=dept.id,
    )
    db_session.add_all([student, technician, admin])
    db_session.commit()

    entities = {
        "dept": dept,
        "cat": cat,
        "student": student,
        "technician": technician,
        "admin": admin,
        "uid": uid,
    }
    yield entities

    # Teardown
    db_session.rollback()
    # Clean up created tickets and related objects
    created_tickets = db_session.scalars(
        select(Ticket).where(Ticket.department_id == dept.id)
    ).all()
    for t in created_tickets:
        db_session.delete(t)
    db_session.commit()

    # Clean up users, categories, departments
    for u in [student, technician, admin]:
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


def test_department_creation_and_uniqueness(db_session):
    uid = uuid.uuid4().hex[:6].upper()
    d1 = Department(
        department_name=f"Unique Department {uid}",
        department_code=f"D_{uid}",
        description="First unique",
    )
    db_session.add(d1)
    db_session.commit()

    # Attempt duplicate department_code
    d2 = Department(
        department_name=f"Different Name {uid}",
        department_code=f"D_{uid}",
    )
    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Cleanup
    db_session.delete(d1)
    db_session.commit()


def test_category_creation_and_department_fk(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]

    assert cat.department_id == dept.id
    assert cat.department.department_name == dept.department_name
    assert cat in dept.categories

    # Invalid department foreign key must fail
    invalid_cat = Category(
        category_name="Invalid Category",
        department_id=9999999,
    )
    db_session.add(invalid_cat)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ticket_creation_and_unique_ticket_number(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    uid = test_setup_entities["uid"]

    t_num = f"TCK-{uid}-001"
    sla = datetime.now(timezone.utc) + timedelta(hours=48)

    ticket = Ticket(
        ticket_number=t_num,
        title="Projector in Room 302 not turning on",
        description="During lecture, HDMI input has no display signal.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Academic Block A, Floor 3",
        building="Block A",
        room_number="302",
        qr_code_identifier=f"QR-BLKA-302-{uid}",
        priority=TicketPriority.HIGH.value,
        status=TicketStatus.SUBMITTED.value,
        sla_deadline=sla,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    assert ticket.id is not None
    assert ticket.ticket_number == t_num
    assert ticket.building == "Block A"
    assert ticket.room_number == "302"
    assert ticket.qr_code_identifier == f"QR-BLKA-302-{uid}"
    assert ticket.creator.id == student.id

    # Duplicate ticket number must fail
    dup_ticket = Ticket(
        ticket_number=t_num,
        title="Duplicate Number",
        description="Test duplicate",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Anywhere",
    )
    db_session.add(dup_ticket)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ticket_assignment_and_relationships(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    technician = test_setup_entities["technician"]
    uid = test_setup_entities["uid"]

    ticket = Ticket(
        ticket_number=f"TCK-{uid}-002",
        title="AC Unit Leaking Water",
        description="Water dripping near lab workstations.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Computer Lab 1",
        building="Tech Tower",
        room_number="Lab 101",
        priority=TicketPriority.MEDIUM.value,
        status=TicketStatus.SUBMITTED.value,
    )
    db_session.add(ticket)
    db_session.commit()

    # Assign ticket to technician
    ticket.assigned_to_id = technician.id
    ticket.status = TicketStatus.ASSIGNED.value
    db_session.commit()
    db_session.refresh(ticket)

    assert ticket.assignee is not None
    assert ticket.assignee.id == technician.id
    assert ticket in technician.assigned_tickets
    assert ticket in student.created_tickets


def test_ticket_comments_and_internal_notes(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    technician = test_setup_entities["technician"]
    uid = test_setup_entities["uid"]

    ticket = Ticket(
        ticket_number=f"TCK-{uid}-003",
        title="Wi-Fi Router Reset Needed",
        description="Wi-Fi coverage is unstable in reading room.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Library Floor 2",
    )
    db_session.add(ticket)
    db_session.commit()

    # Public comment from student
    public_comment = TicketComment(
        ticket_id=ticket.id,
        user_id=student.id,
        comment="Could someone check before 2 PM? We have a group study.",
        is_internal=False,
    )
    # Internal note from technician
    internal_note = TicketComment(
        ticket_id=ticket.id,
        user_id=technician.id,
        comment="Hardware reboot needed on AP-04; firmware upgrade pending.",
        is_internal=True,
    )
    db_session.add_all([public_comment, internal_note])
    db_session.commit()
    db_session.refresh(ticket)

    assert len(ticket.comments) == 2
    comments = sorted(ticket.comments, key=lambda c: c.is_internal)
    assert comments[0].is_internal is False
    assert comments[0].user.id == student.id
    assert comments[1].is_internal is True
    assert comments[1].user.id == technician.id


def test_ticket_status_history_tracking(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    admin = test_setup_entities["admin"]
    uid = test_setup_entities["uid"]

    ticket = Ticket(
        ticket_number=f"TCK-{uid}-004",
        title="Broken Chair in Room 204",
        description="Leg broken on desk chair.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Room 204",
    )
    db_session.add(ticket)
    db_session.commit()

    # Record history when reviewed
    h1 = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=admin.id,
        old_status=TicketStatus.SUBMITTED.value,
        new_status=TicketStatus.UNDER_REVIEW.value,
        remarks="Ticket reviewed by admin, ready for technician assignment.",
    )
    # Record history when assigned
    h2 = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=admin.id,
        old_status=TicketStatus.UNDER_REVIEW.value,
        new_status=TicketStatus.ASSIGNED.value,
        remarks="Assigned to campus maintenance crew.",
    )
    db_session.add_all([h1, h2])
    db_session.commit()
    db_session.refresh(ticket)

    assert len(ticket.history) == 2
    assert ticket.history[0].new_status == TicketStatus.UNDER_REVIEW.value
    assert ticket.history[1].new_status == TicketStatus.ASSIGNED.value
    assert ticket.history[0].changed_by.id == admin.id


def test_attachment_metadata(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    uid = test_setup_entities["uid"]

    ticket = Ticket(
        ticket_number=f"TCK-{uid}-005",
        title="Water leak in restroom",
        description="Photo attached showing pipe connection leak.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Ground Floor Restroom",
    )
    db_session.add(ticket)
    db_session.commit()

    stored_file = f"attachment_{uid}_{uuid.uuid4().hex[:6]}.jpg"
    attachment = Attachment(
        ticket_id=ticket.id,
        uploaded_by_id=student.id,
        original_filename="leak_photo.jpg",
        stored_filename=stored_file,
        file_type="image/jpeg",
        file_size=1024 * 350,  # 350 KB
        storage_path=f"uploads/tickets/{stored_file}",
    )
    db_session.add(attachment)
    db_session.commit()
    db_session.refresh(ticket)

    assert len(ticket.attachments) == 1
    att = ticket.attachments[0]
    assert att.original_filename == "leak_photo.jpg"
    assert att.file_size == 358400
    assert att.uploaded_by.id == student.id

    # Duplicate stored_filename must fail
    dup_att = Attachment(
        ticket_id=ticket.id,
        uploaded_by_id=student.id,
        original_filename="another_name.jpg",
        stored_filename=stored_file,
        file_type="image/jpeg",
        file_size=200,
        storage_path=f"uploads/{stored_file}",
    )
    db_session.add(dup_att)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_notification_creation_and_reading(db_session, test_setup_entities):
    student = test_setup_entities["student"]

    notification = Notification(
        user_id=student.id,
        title="Ticket TCK-101 Assigned",
        message="A technician has been assigned to your request.",
        notification_type="ticket_assigned",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(student)

    assert len(student.notifications) >= 1
    notif = [n for n in student.notifications if n.id == notification.id][0]
    assert notif.is_read is False

    # Mark as read
    notif.is_read = True
    db_session.commit()
    db_session.refresh(notif)
    assert notif.is_read is True


def test_knowledge_base_creation(db_session, test_setup_entities):
    cat = test_setup_entities["cat"]
    admin = test_setup_entities["admin"]

    kb_article = KnowledgeBase(
        title="How to connect to Campus eduroam Wi-Fi",
        content="Step 1: Select 'eduroam' network. Step 2: Enter campus credentials...",
        category_id=cat.id,
        created_by_id=admin.id,
        is_published=True,
    )
    db_session.add(kb_article)
    db_session.commit()
    db_session.refresh(kb_article)

    assert kb_article.id is not None
    assert kb_article.category.id == cat.id
    assert kb_article.author.id == admin.id
    assert kb_article.is_published is True

    # Cleanup
    db_session.delete(kb_article)
    db_session.commit()


def test_cascade_delete_ticket_removes_dependent_records(db_session, test_setup_entities):
    dept = test_setup_entities["dept"]
    cat = test_setup_entities["cat"]
    student = test_setup_entities["student"]
    uid = test_setup_entities["uid"]

    ticket = Ticket(
        ticket_number=f"TCK-{uid}-CASCADE",
        title="Cascade Test Ticket",
        description="Testing cascade delete behavior.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=student.id,
        location="Test Location",
    )
    db_session.add(ticket)
    db_session.commit()

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=student.id,
        comment="Comment to be cascaded",
    )
    history = TicketHistory(
        ticket_id=ticket.id,
        changed_by_id=student.id,
        old_status=None,
        new_status=TicketStatus.SUBMITTED.value,
    )
    attachment = Attachment(
        ticket_id=ticket.id,
        uploaded_by_id=student.id,
        original_filename="cascade.pdf",
        stored_filename=f"cascade_{uid}.pdf",
        file_type="application/pdf",
        file_size=5000,
        storage_path=f"uploads/{uid}.pdf",
    )
    db_session.add_all([comment, history, attachment])
    db_session.commit()

    ticket_id = ticket.id
    comment_id = comment.id
    history_id = history.id
    attachment_id = attachment.id

    # Delete the ticket
    db_session.delete(ticket)
    db_session.commit()

    # Verify dependents were automatically cascaded
    assert db_session.get(TicketComment, comment_id) is None
    assert db_session.get(TicketHistory, history_id) is None
    assert db_session.get(Attachment, attachment_id) is None
