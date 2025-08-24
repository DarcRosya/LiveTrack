from typing import TYPE_CHECKING
from pydantic import BaseModel, computed_field
from datetime import datetime, timezone

from models.habit import HabitStatus


if TYPE_CHECKING:
    from models.habit import Habit


class HabitRead(BaseModel):
    id: int
    name: str
    started_at: datetime # This field we receive from DB
    is_active: bool
    duration_days: int
    
    @computed_field
    @property
    def status(self) -> HabitStatus:
        if not self.is_active:
            return HabitStatus.DEACTIVATED
        
        if self.duration_days < 3:
            return HabitStatus.NEW
        else:
            return HabitStatus.ACTIVE

    class Config:
        from_attributes = True # Allows Pydantic to read data from ORM models