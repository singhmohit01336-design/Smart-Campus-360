from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.category import Category
from app.models.department import Department
from app.models.user import User, UserRole


router = APIRouter(
    tags=["Departments & Metadata"],
)


class DepartmentItem(BaseModel):
    id: int
    department_name: str
    department_code: str
    description: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryItem(BaseModel):
    id: int
    category_name: str
    department_id: int
    description: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TechnicianItem(BaseModel):
    id: int
    full_name: str
    email: str
    institutional_id: str | None = None
    department_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/departments/",
    response_model=list[DepartmentItem],
)
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List active departments for complaint filing and routing."""
    return db.scalars(
        select(Department).where(Department.is_active == True).order_by(Department.department_name.asc())
    ).all()


@router.get(
    "/categories/",
    response_model=list[CategoryItem],
)
def list_categories(
    department_id: int | None = Query(default=None, description="Filter categories by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List active complaint categories, optionally filtered by department."""
    query = select(Category).where(Category.is_active == True)
    if department_id:
        query = query.where(Category.department_id == department_id)
    return db.scalars(query.order_by(Category.category_name.asc())).all()


@router.get(
    "/technicians/",
    response_model=list[TechnicianItem],
)
def list_active_technicians(
    department_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List active campus technicians for ticket assignment."""
    query = select(User).where(
        User.role == UserRole.TECHNICIAN.value,
        User.is_active == True,
    )
    if department_id:
        query = query.where(User.department_id == department_id)
    return db.scalars(query.order_by(User.full_name.asc())).all()
