from typing import TYPE_CHECKING, List
import enum 

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey


from core.database import Base
from core.mixins import TimestampMixin
from core.db_types import intpk, str_50, str_256, aware_datetime


if TYPE_CHECKING:
    from .user import User
    from .tag import Tag


class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str_50]
    description: Mapped[str_256]
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)

    deadline: Mapped[aware_datetime] = mapped_column(nullable=True)
    completed_at: Mapped[aware_datetime] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(
        back_populates="tasks"
    )

    tags: Mapped[List["Tag"]] = relationship(
        back_populates="tasks",
        secondary="task_tags"
    )