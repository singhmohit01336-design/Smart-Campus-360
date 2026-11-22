from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.ticket import Ticket
    from app.models.knowledge_base import KnowledgeBase


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    category_name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
    department: Mapped["Department"] = relationship(
        "Department", back_populates="categories"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="category"
    )
    knowledge_items: Mapped[list["KnowledgeBase"]] = relationship(
        "KnowledgeBase", back_populates="category"
    )
