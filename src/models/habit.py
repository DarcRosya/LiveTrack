from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import ForeignKey, func, case 
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from src.core.database import Base
from src.core.db_types import intpk, str_50, aware_datetime
from src.core.mixins import TimestampMixin


if TYPE_CHECKING:
    from .user import User


# for pydantic schema 
class HabitStatus(enum.Enum):
    NEW = "new"                         # active < 3 days
    ACTIVE = "active"                   # active >= 3 days
    DEACTIVATED = "deactivated"         # active count need to be reseted 


class Habit(Base, TimestampMixin):
    __tablename__ = "habits"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    name: Mapped[str_50]

    started_at: Mapped[aware_datetime] = mapped_column(server_default=func.now())
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    timer_to_notify_in_seconds: Mapped[int] = mapped_column(default=600)

    @hybrid_property
    def duration_days(self) -> int:
        """This part works in Python when you already have a Habit object."""
        # We return 0 for inactive habits to avoid confusion.
        if not self.is_active:
            return 0
        return (datetime.now(timezone.utc) - self.started_at).days

    @duration_days.expression
    def duration_days(cls):
        """This part will be translated into SQL for queries."""
        # We use CASE to return 0 for inactive habits in SQL as well.
        return func.floor(
            case(
                (cls.is_active, func.extract('epoch', func.now() - cls.started_at) / 86400),
                else_=0
            )
        )

    user: Mapped["User"] = relationship(
        back_populates="habits",
    )