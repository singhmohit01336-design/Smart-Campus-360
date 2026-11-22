import uuid
import pytest
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import get_current_active_user, require_roles
from app.core.security import create_access_token, hash_password
from app.core.seed import seed_database
from app.models.user import User, UserRole
from app.models.department import Department


# Setup test router with role-guarded endpoints
test_router = APIRouter(prefix="/test-rbac", tags=["RBAC-Test"])


@test_router.get("/student-only")
def student_route(user: User = Depends(require_roles([UserRole.STUDENT]))):
    return {"message": "student access granted", "role": user.role}


@test_router.get("/faculty-only")
def faculty_route(user: User = Depends(require_roles([UserRole.FACULTY]))):
    return {"message": "faculty access granted", "role": user.role}


@test_router.get("/technician-only")
def technician_route(user: User = Depends(require_roles([UserRole.TECHNICIAN]))):
    return {"message": "technician access granted", "role": user.role}


@test_router.get("/admin-only")
def admin_route(user: User = Depends(require_roles([UserRole.ADMIN]))):
    return {"message": "admin access granted", "role": user.role}


@test_router.get("/superadmin-only")
def superadmin_route(user: User = Depends(require_roles([UserRole.SUPERADMIN]))):
    return {"message": "superadmin access granted", "role": user.role}


@test_router.get("/staff-only")
def staff_route(
    user: User = Depends(require_roles([UserRole.ADMIN, UserRole.TECHNICIAN]))
):
    return {"message": "staff access granted", "role": user.role}


# Include test router in app for testing
@pytest.fixture(autouse=True, scope="module")
def register_rbac_test_routes():
    from app.main import app
    app.include_router(test_router)


def test_user_role_enum_values():
    assert UserRole.STUDENT.value == "student"
    assert UserRole.FACULTY.value == "faculty"
    assert UserRole.TECHNICIAN.value == "technician"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.SUPERADMIN.value == "superadmin"
    assert len(UserRole) == 5


def test_unauthenticated_request_rejected(client):
    response = client.get("/test-rbac/admin-only")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_role_allowed_and_denied_permissions(client, db_session):
    # Retrieve demo users seeded in db
    users_by_role = {}
    for role_enum in UserRole:
        user = db_session.scalar(
            select(User).where(User.role == role_enum.value)
        )
        assert user is not None, f"Seeded user for role {role_enum.value} should exist"
        users_by_role[role_enum.value] = user

    def auth_header(u: User):
        token = create_access_token({"sub": str(u.id), "role": u.role})
        return {"Authorization": f"Bearer {token}"}

    student_headers = auth_header(users_by_role["student"])
    faculty_headers = auth_header(users_by_role["faculty"])
    technician_headers = auth_header(users_by_role["technician"])
    admin_headers = auth_header(users_by_role["admin"])
    superadmin_headers = auth_header(users_by_role["superadmin"])

    # 1. Student access: allowed to student-only, forbidden to admin/faculty/technician
    assert client.get("/test-rbac/student-only", headers=student_headers).status_code == 200
    assert client.get("/test-rbac/admin-only", headers=student_headers).status_code == 403
    assert client.get("/test-rbac/faculty-only", headers=student_headers).status_code == 403
    assert client.get("/test-rbac/technician-only", headers=student_headers).status_code == 403

    # 2. Faculty access: allowed to faculty-only, forbidden to admin/technician/student
    assert client.get("/test-rbac/faculty-only", headers=faculty_headers).status_code == 200
    assert client.get("/test-rbac/admin-only", headers=faculty_headers).status_code == 403
    assert client.get("/test-rbac/technician-only", headers=faculty_headers).status_code == 403
    assert client.get("/test-rbac/student-only", headers=faculty_headers).status_code == 403

    # 3. Technician access: allowed to technician-only & staff-only, forbidden to admin/student
    assert client.get("/test-rbac/technician-only", headers=technician_headers).status_code == 200
    assert client.get("/test-rbac/staff-only", headers=technician_headers).status_code == 200
    assert client.get("/test-rbac/admin-only", headers=technician_headers).status_code == 403
    assert client.get("/test-rbac/student-only", headers=technician_headers).status_code == 403

    # 4. Admin access: allowed to admin-only & staff-only, forbidden to technician-only/student-only
    assert client.get("/test-rbac/admin-only", headers=admin_headers).status_code == 200
    assert client.get("/test-rbac/staff-only", headers=admin_headers).status_code == 200
    assert client.get("/test-rbac/technician-only", headers=admin_headers).status_code == 403
    assert client.get("/test-rbac/student-only", headers=admin_headers).status_code == 403

    # 5. Superadmin explicit universal access
    assert client.get("/test-rbac/superadmin-only", headers=superadmin_headers).status_code == 200
    assert client.get("/test-rbac/admin-only", headers=superadmin_headers).status_code == 200
    assert client.get("/test-rbac/faculty-only", headers=superadmin_headers).status_code == 200
    assert client.get("/test-rbac/technician-only", headers=superadmin_headers).status_code == 200
    assert client.get("/test-rbac/student-only", headers=superadmin_headers).status_code == 200
    assert client.get("/test-rbac/staff-only", headers=superadmin_headers).status_code == 200


def test_inactive_user_access_blocked(client, db_session):
    unique_id = uuid.uuid4().hex[:8]
    inactive_user = User(
        full_name="Inactive User",
        email=f"inactive_{unique_id}@example.com",
        hashed_password=hash_password("Password123!#"),
        role=UserRole.STUDENT.value,
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()
    db_session.refresh(inactive_user)

    try:
        token = create_access_token({"sub": str(inactive_user.id), "role": inactive_user.role})
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/test-rbac/student-only", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Account is inactive"
    finally:
        db_session.delete(inactive_user)
        db_session.commit()


def test_public_registration_cannot_set_admin_role(client, db_session):
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"attacker_{unique_id}@example.com"
    payload = {
        "full_name": "Privilege Escalation Attempt",
        "email": test_email,
        "password": "StrongPassword123!",
        "role": "superadmin",  # Attacker attempts to pass superadmin
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "student"  # Server strictly assigned student!

    created_user_id = data["id"]
    try:
        user_in_db = db_session.scalar(select(User).where(User.id == created_user_id))
        assert user_in_db is not None
        assert user_in_db.role == UserRole.STUDENT.value
    finally:
        db_session.delete(user_in_db)
        db_session.commit()


def test_seeding_idempotency_and_preservation():
    result = seed_database()
    assert result["status"] == "success"
    assert len(result["created_users"]) == 0
    assert len(result["skipped_users"]) == 5
    assert len(result["created_departments"]) == 0
    assert len(result["skipped_departments"]) == 4
