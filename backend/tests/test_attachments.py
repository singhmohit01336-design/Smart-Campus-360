import io
import uuid
import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.category import Category
from app.models.department import Department
from app.models.ticket import Ticket
from app.models.attachment import Attachment
from app.models.user import User, UserRole


@pytest.fixture
def attachment_test_context(db_session):
    uid = uuid.uuid4().hex[:6]

    dept = Department(
        department_name=f"Attachment Dept {uid}",
        department_code=f"AD_{uid.upper()}",
        is_active=True,
    )
    db_session.add(dept)
    db_session.flush()

    cat = Category(
        category_name=f"Attachment Cat {uid}",
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(cat)

    creator_student = User(
        full_name=f"Attachment Creator {uid}",
        email=f"att_creator_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    other_student = User(
        full_name=f"Att Intruder {uid}",
        email=f"att_intruder_{uid}@example.com",
        hashed_password="hash",
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    db_session.add_all([creator_student, other_student])
    db_session.commit()

    ticket = Ticket(
        ticket_number=f"TCK-ATT-{uid}",
        title="Fluorescent bulb flickering violently",
        description="Room 101 fixture is flashing continuously.",
        category_id=cat.id,
        department_id=dept.id,
        created_by_id=creator_student.id,
        location="Room 101",
    )
    db_session.add(ticket)
    db_session.commit()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    ctx = {
        "dept": dept,
        "cat": cat,
        "creator": creator_student,
        "other": other_student,
        "ticket": ticket,
        "h_creator": token_for(creator_student),
        "h_other": token_for(other_student),
    }
    yield ctx

    # Cleanup
    db_session.rollback()
    t = db_session.get(Ticket, ticket.id)
    if t:
        db_session.delete(t)
    db_session.commit()

    for u in [creator_student, other_student]:
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


def test_valid_file_uploads(client, attachment_test_context):
    ctx = attachment_test_context
    t_id = ctx["ticket"].id

    # 1. Valid PNG upload
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    files = {"file": ("screenshot.png", io.BytesIO(png_bytes), "image/png")}
    resp_png = client.post(f"/tickets/{t_id}/attachments/", files=files, headers=ctx["h_creator"])
    assert resp_png.status_code == 201
    png_data = resp_png.json()
    assert png_data["original_filename"] == "screenshot.png"
    assert png_data["file_type"] == "image/png"
    assert png_data["download_url"].startswith(f"/tickets/{t_id}/attachments/")

    # 2. Valid PDF upload
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    files = {"file": ("manual.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    resp_pdf = client.post(f"/tickets/{t_id}/attachments/", files=files, headers=ctx["h_creator"])
    assert resp_pdf.status_code == 201
    assert resp_pdf.json()["file_type"] == "application/pdf"

    # 3. Valid JPEG upload
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"
    files = {"file": ("photo.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
    resp_jpg = client.post(f"/tickets/{t_id}/attachments/", files=files, headers=ctx["h_creator"])
    assert resp_jpg.status_code == 201
    assert resp_jpg.json()["file_type"] == "image/jpeg"


def test_invalid_file_uploads_rejected(client, attachment_test_context):
    ctx = attachment_test_context
    t_id = ctx["ticket"].id

    # 1. Executable file extension
    exe_file = {"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")}
    assert client.post(f"/tickets/{t_id}/attachments/", files=exe_file, headers=ctx["h_creator"]).status_code == 400

    # 2. Spoofed extension: named .png but header is plain text
    spoofed_file = {"file": ("fake.png", io.BytesIO(b"Hello world, I am not a png image!"), "image/png")}
    resp_spoof = client.post(f"/tickets/{t_id}/attachments/", files=spoofed_file, headers=ctx["h_creator"])
    assert resp_spoof.status_code == 400
    assert "signature" in resp_spoof.json()["detail"].lower()

    # 3. Empty file (0 bytes)
    empty_file = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    assert client.post(f"/tickets/{t_id}/attachments/", files=empty_file, headers=ctx["h_creator"]).status_code == 400

    # 4. Oversized file (> 5 MB)
    large_bytes = b"%PDF" + b"A" * (5 * 1024 * 1024 + 10)
    oversized_file = {"file": ("large.pdf", io.BytesIO(large_bytes), "application/pdf")}
    resp_large = client.post(f"/tickets/{t_id}/attachments/", files=oversized_file, headers=ctx["h_creator"])
    assert resp_large.status_code == 400
    assert "exceeds maximum limit" in resp_large.json()["detail"].lower()


def test_download_attachment_authorization(client, attachment_test_context):
    ctx = attachment_test_context
    t_id = ctx["ticket"].id

    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    files = {"file": ("sample.png", io.BytesIO(png_bytes), "image/png")}
    upload_resp = client.post(f"/tickets/{t_id}/attachments/", files=files, headers=ctx["h_creator"])
    assert upload_resp.status_code == 201
    att_id = upload_resp.json()["id"]

    # 1. Creator downloads file -> 200 OK
    down_resp = client.get(f"/tickets/{t_id}/attachments/{att_id}/download", headers=ctx["h_creator"])
    assert down_resp.status_code == 200
    assert down_resp.content == png_bytes

    # 2. Unauthorized third-party student attempts download -> 403 Forbidden
    assert client.get(f"/tickets/{t_id}/attachments/{att_id}/download", headers=ctx["h_other"]).status_code == 403

    # 3. Unauthenticated request -> 401 Unauthorized
    assert client.get(f"/tickets/{t_id}/attachments/{att_id}/download").status_code == 401

    # 4. Nonexistent attachment ID -> 404
    assert client.get(f"/tickets/{t_id}/attachments/99999/download", headers=ctx["h_creator"]).status_code == 404
