from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from src.core.database import Base
from src.core.db_types import intpk, str_50


if TYPE_CHECKING: 
    from .user import User
    from .task import Task


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str_50]

    user: Mapped["User"] = relationship(
        back_populates="tags",
    )

    tasks: Mapped[List["Task"]] = relationship(
        back_populates="tags",
        secondary="task_tags"
    )


class TaskTags(Base):
    __tablename__ = "task_tags"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )