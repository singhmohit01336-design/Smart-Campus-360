from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.ticket import Ticket
    from app.models.notification import Notification


class UserRole(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    TECHNICIAN = "technician"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(30), nullable=False, default=UserRole.STUDENT.value
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    department_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="users"
    )
    created_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="[Ticket.created_by_id]",
        back_populates="creator",
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="[Ticket.assigned_to_id]",
        back_populates="assignee",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
