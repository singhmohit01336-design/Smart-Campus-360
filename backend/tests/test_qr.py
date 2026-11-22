import pytest
from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.location import CampusLocation
from app.models.ticket import Ticket
from app.models.user import User, UserRole


@pytest.fixture
def qr_test_context(db_session):
    student = db_session.query(User).filter(User.role == UserRole.STUDENT.value).first()
    dept = db_session.query(Department).filter(Department.department_code == "IT").first()
    cat = db_session.query(Category).filter(Category.department_id == dept.id).first()
    loc = db_session.query(CampusLocation).filter(CampusLocation.qr_code_identifier == "QR-TECH-LAB101").first()

    token = create_access_token({"sub": str(student.id), "role": student.role})
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "student": student,
        "dept": dept,
        "cat": cat,
        "loc": loc,
        "headers": headers,
    }


def test_resolve_qr_location_success(client, qr_test_context):
    ctx = qr_test_context
    response = client.get(f"/qr/{ctx['loc'].qr_code_identifier}", headers=ctx["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["qr_code_identifier"] == "QR-TECH-LAB101"
    assert data["building"] == "Tech Tower"
    assert data["room_number"] == "Lab 101"
    assert data["department_name"] == "Information Technology"


def test_list_campus_locations(client, qr_test_context):
    ctx = qr_test_context
    response = client.get("/qr/locations", headers=ctx["headers"])
    assert response.status_code == 200
    locations = response.json()
    assert isinstance(locations, list)
    assert len(locations) >= 1
    assert any(loc["qr_code_identifier"] == "QR-TECH-LAB101" for loc in locations)


def test_resolve_invalid_qr_location(client, qr_test_context):
    ctx = qr_test_context
    response = client.get("/qr/INVALID-QR-CODE-999", headers=ctx["headers"])
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_submit_qr_complaint_auto_populates_location(client, qr_test_context, db_session):
    ctx = qr_test_context
    payload = {
        "qr_code_identifier": ctx["loc"].qr_code_identifier,
        "title": "Workstation 14 Keyboard Missing Spacebar",
        "description": "The keycap is detached and membrane does not register keystrokes.",
        "category_id": ctx["cat"].id,
        "priority": "medium",
    }
    response = client.post("/qr/tickets", json=payload, headers=ctx["headers"])
    assert response.status_code == 201
    ticket_data = response.json()

    assert ticket_data["qr_code_identifier"] == "QR-TECH-LAB101"
    assert ticket_data["building"] == "Tech Tower"
    assert ticket_data["room_number"] == "Lab 101"
    assert ticket_data["location"] == "Computer Science Lab 101"
    assert ticket_data["status"] == "submitted"
    assert ticket_data["created_by_id"] == ctx["student"].id

    # Cleanup created ticket
    t_obj = db_session.get(Ticket, ticket_data["id"])
    if t_obj:
        db_session.delete(t_obj)
        db_session.commit()


def test_submit_qr_complaint_invalid_qr_rejected(client, qr_test_context):
    ctx = qr_test_context
    payload = {
        "qr_code_identifier": "FAKE-QR-CODE-XYZ",
        "title": "Complaint on fake QR",
        "description": "This should be rejected because QR does not exist.",
        "category_id": ctx["cat"].id,
    }
    response = client.post("/qr/tickets", json=payload, headers=ctx["headers"])
    assert response.status_code == 404
    assert "invalid or inactive" in response.json()["detail"].lower()
