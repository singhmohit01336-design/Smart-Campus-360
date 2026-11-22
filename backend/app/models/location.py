from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department


class CampusLocation(Base):
    __tablename__ = "campus_locations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    qr_code_identifier: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    building: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    room_number: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    floor: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    location_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
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
    department: Mapped["Department | None"] = relationship(
        "Department"
    )
