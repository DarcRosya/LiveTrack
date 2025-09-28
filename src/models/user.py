from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.mixins import TimestampMixin
from src.core.db_types import intpk, str_50, str_256


if TYPE_CHECKING:
    from .task import Task
    from .habit import Habit
    from .tag import Tag


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[intpk]
    username: Mapped[str_50] = mapped_column(unique=True, index=True)
    email: Mapped[str_256] = mapped_column(unique=True, index=True)
    password_in_hash: Mapped[str]

    is_active_account: Mapped[bool] = mapped_column(default=False)

    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)

    tasks: Mapped[List["Task"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    habits: Mapped[List["Habit"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tags: Mapped[List["Tag"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
