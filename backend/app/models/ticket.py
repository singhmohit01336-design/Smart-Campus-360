from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.category import Category
    from app.models.user import User
    from app.models.comment import TicketComment
    from app.models.history import TicketHistory
    from app.models.attachment import Attachment


class TicketStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    ticket_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Location & Classroom QR details
    location: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    building: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    room_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    qr_code_identifier: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    priority: Mapped[str] = mapped_column(
        String(20), default=TicketPriority.MEDIUM.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default=TicketStatus.SUBMITTED.value, nullable=False
    )
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category", back_populates="tickets"
    )
    department: Mapped["Department"] = relationship(
        "Department", back_populates="tickets"
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_tickets",
    )
    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_tickets",
    )
    comments: Mapped[list["TicketComment"]] = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    history: Mapped[list["TicketHistory"]] = relationship(
        "TicketHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
