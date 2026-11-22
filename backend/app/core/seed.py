import os
import sys
from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.department import Department


# Default demo password for local development environments
DEFAULT_LOCAL_DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "CampusDemo2026!#")

DEMO_DEPARTMENTS = [
    {
        "department_name": "Information Technology",
        "department_code": "IT",
        "description": "Campus IT services, networking, software, and lab computing",
    },
    {
        "department_name": "Estate & Maintenance",
        "department_code": "ESTATE",
        "description": "Facilities maintenance, civil repairs, and plumbing",
    },
    {
        "department_name": "Electrical & Power",
        "department_code": "ELEC",
        "description": "Electrical infrastructure, power backups, and air conditioning",
    },
    {
        "department_name": "Academic Affairs",
        "department_code": "ACAD",
        "description": "Classroom equipment, lecture halls, and academic amenities",
    },
]

DEMO_USERS = [
    {
        "email": "superadmin@smartcampus360.edu",
        "full_name": "Campus Super Admin",
        "role": UserRole.SUPERADMIN.value,
        "phone_number": "+919876543210",
        "department_code": "IT",
    },
    {
        "email": "admin@smartcampus360.edu",
        "full_name": "Campus Admin",
        "role": UserRole.ADMIN.value,
        "phone_number": "+919876543211",
        "department_code": "ESTATE",
    },
    {
        "email": "technician@smartcampus360.edu",
        "full_name": "Campus Lead Technician",
        "role": UserRole.TECHNICIAN.value,
        "phone_number": "+919876543212",
        "department_code": "ELEC",
    },
    {
        "email": "faculty@smartcampus360.edu",
        "full_name": "Campus Faculty Member",
        "role": UserRole.FACULTY.value,
        "phone_number": "+919876543213",
        "department_code": "ACAD",
    },
    {
        "email": "student@smartcampus360.edu",
        "full_name": "Campus Student",
        "role": UserRole.STUDENT.value,
        "phone_number": "+919876543214",
        "department_code": None,
    },
]


def seed_database(force: bool = False) -> dict:
    """
    Idempotent database seeding for development and staging environments.
    Never overwrites existing records or passwords.
    Never runs automatically in production.
    """
    if settings.ENVIRONMENT.lower() == "production" and not force:
        print("[SEED] Safety Notice: Cannot automatically seed demo accounts in production.")
        return {
            "status": "aborted",
            "message": "Seeding blocked in production environment.",
        }

    db = SessionLocal()
    created_departments = []
    skipped_departments = []
    created_users = []
    skipped_users = []

    try:
        # 1. Seed Departments (idempotent)
        dept_lookup = {}
        for dept_data in DEMO_DEPARTMENTS:
            existing_dept = db.scalar(
                select(Department).where(
                    Department.department_code == dept_data["department_code"]
                )
            )
            if existing_dept:
                skipped_departments.append(existing_dept.department_code)
                dept_lookup[existing_dept.department_code] = existing_dept.id
            else:
                new_dept = Department(
                    department_name=dept_data["department_name"],
                    department_code=dept_data["department_code"],
                    description=dept_data["description"],
                    is_active=True,
                )
                db.add(new_dept)
                db.flush()
                created_departments.append(new_dept.department_code)
                dept_lookup[new_dept.department_code] = new_dept.id

        # 2. Seed Demo Users (idempotent)
        for user_data in DEMO_USERS:
            existing_user = db.scalar(
                select(User).where(User.email == user_data["email"])
            )
            if existing_user:
                skipped_users.append(existing_user.email)
            else:
                dept_id = None
                if user_data.get("department_code"):
                    dept_id = dept_lookup.get(user_data["department_code"])

                new_user = User(
                    full_name=user_data["full_name"],
                    email=user_data["email"],
                    hashed_password=hash_password(DEFAULT_LOCAL_DEMO_PASSWORD),
                    role=user_data["role"],
                    phone_number=user_data.get("phone_number"),
                    department_id=dept_id,
                    is_active=True,
                )
                db.add(new_user)
                created_users.append(user_data["email"])

        db.commit()

        summary = {
            "status": "success",
            "created_departments": created_departments,
            "skipped_departments": skipped_departments,
            "created_users": created_users,
            "skipped_users": skipped_users,
        }
        return summary

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    result = seed_database(force=force_run)
    print("Seed execution result:", result)
