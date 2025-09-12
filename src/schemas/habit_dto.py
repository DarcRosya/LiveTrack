from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel, computed_field
from datetime import datetime

from src.models.habit import HabitStatus


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


class HabitCreate(BaseModel):
    name: str
    is_active: bool
    timer_to_notify_in_seconds: int # on client side we will request in minutes afterwards convert in seconds


class HabitUpdate(BaseModel):
    name: Optional[str]
    is_active: Optional[bool]
    timer_to_notify_in_seconds: Optional[int]