from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.comment import TicketComment
from app.models.history import TicketHistory
from app.models.attachment import Attachment
from app.models.notification import Notification
from app.models.knowledge_base import KnowledgeBase
from app.models.location import CampusLocation

__all__ = [
    "User",
    "UserRole",
    "Department",
    "Category",
    "Ticket",
    "TicketStatus",
    "TicketPriority",
    "TicketComment",
    "TicketHistory",
    "Attachment",
    "Notification",
    "KnowledgeBase",
    "CampusLocation",
]
