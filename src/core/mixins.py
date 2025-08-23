from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from .db_types import aware_datetime

class TimestampMixin:
    """Mixin for automatically adding the created_at and updated_at fields."""
    created_at: Mapped[aware_datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),  # func.now() in PostgreSQL for TIMESTAMPTZ works correctly,
                                   # since the DBMS will return the current time in UTC itself.
    )
    
    updated_at: Mapped[aware_datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )