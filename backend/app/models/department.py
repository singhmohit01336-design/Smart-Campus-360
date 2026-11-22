from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.ticket import Ticket


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    department_name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    department_code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="department"
    )
    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="department", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="department"
    )
