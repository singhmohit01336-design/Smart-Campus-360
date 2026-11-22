import os
import sys
from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.location import CampusLocation


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

DEMO_CATEGORIES = [
    {"category_name": "Internet & Wi-Fi", "department_code": "IT", "description": "Campus Wi-Fi, Ethernet, and connectivity issues"},
    {"category_name": "Lab Computers & Workstations", "department_code": "IT", "description": "Lab hardware, PC peripherals, and operating systems"},
    {"category_name": "Software & Campus Portal", "department_code": "IT", "description": "Student portal, email, and campus software licenses"},
    {"category_name": "Plumbing & Restroom", "department_code": "ESTATE", "description": "Water leaks, washroom fittings, and drainage"},
    {"category_name": "Furniture & Carpentry", "department_code": "ESTATE", "description": "Broken desks, chairs, doors, and window latches"},
    {"category_name": "Housekeeping & Cleaning", "department_code": "ESTATE", "description": "Waste disposal, sanitation, and cleanliness"},
    {"category_name": "Lighting & Electrical Supply", "department_code": "ELEC", "description": "Bulbs, tubes, fans, wall sockets, and tripping breakers"},
    {"category_name": "Air Conditioning & HVAC", "department_code": "ELEC", "description": "Classroom and lab AC cooling failures"},
    {"category_name": "Projector & Smart Board", "department_code": "ACAD", "description": "Classroom projectors, screens, and podium systems"},
    {"category_name": "Audio & Microphone", "department_code": "ACAD", "description": "Microphones, speakers, and PA systems in lecture halls"},
]

DEMO_LOCATIONS = [
    {
        "qr_code_identifier": "QR-TECH-LAB101",
        "building": "Tech Tower",
        "room_number": "Lab 101",
        "floor": "1st Floor",
        "location_name": "Computer Science Lab 101",
        "department_code": "IT",
    },
    {
        "qr_code_identifier": "QR-ACAD-302",
        "building": "Academic Block A",
        "room_number": "302",
        "floor": "3rd Floor",
        "location_name": "Smart Classroom 302",
        "department_code": "ACAD",
    },
    {
        "qr_code_identifier": "QR-ELEC-PWR2",
        "building": "Utility Block",
        "room_number": "PWR-02",
        "floor": "Ground Floor",
        "location_name": "Main Substation & UPS Room",
        "department_code": "ELEC",
    },
    {
        "qr_code_identifier": "QR-EST-REST1",
        "building": "Central Library",
        "room_number": "G-05",
        "floor": "Ground Floor",
        "location_name": "Library Ground Restroom Facility",
        "department_code": "ESTATE",
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
    created_categories = []
    skipped_categories = []
    created_locations = []
    skipped_locations = []
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

        # 2. Seed Categories (idempotent)
        for cat_data in DEMO_CATEGORIES:
            dept_id = dept_lookup.get(cat_data["department_code"])
            existing_cat = db.scalar(
                select(Category).where(
                    Category.category_name == cat_data["category_name"],
                    Category.department_id == dept_id,
                )
            )
            if existing_cat:
                skipped_categories.append(existing_cat.category_name)
            else:
                new_cat = Category(
                    category_name=cat_data["category_name"],
                    description=cat_data["description"],
                    department_id=dept_id,
                    is_active=True,
                )
                db.add(new_cat)
                created_categories.append(cat_data["category_name"])

        # 3. Seed Campus Locations / QR Codes (idempotent)
        for loc_data in DEMO_LOCATIONS:
            existing_loc = db.scalar(
                select(CampusLocation).where(
                    CampusLocation.qr_code_identifier == loc_data["qr_code_identifier"]
                )
            )
            if existing_loc:
                skipped_locations.append(existing_loc.qr_code_identifier)
            else:
                dept_id = dept_lookup.get(loc_data.get("department_code"))
                new_loc = CampusLocation(
                    qr_code_identifier=loc_data["qr_code_identifier"],
                    building=loc_data["building"],
                    room_number=loc_data["room_number"],
                    floor=loc_data.get("floor"),
                    location_name=loc_data["location_name"],
                    department_id=dept_id,
                    is_active=True,
                )
                db.add(new_loc)
                created_locations.append(loc_data["qr_code_identifier"])

        # 4. Seed Demo Users (idempotent)
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
            "created_categories": created_categories,
            "skipped_categories": skipped_categories,
            "created_locations": created_locations,
            "skipped_locations": skipped_locations,
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
