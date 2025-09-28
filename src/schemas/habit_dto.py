from typing import TYPE_CHECKING, Annotated, Optional
from pydantic import BaseModel, BeforeValidator, computed_field, model_validator
from datetime import datetime

from src.models.habit import HabitStatus
from src.utils.validators import strip_string


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
    name: Annotated[str, BeforeValidator(strip_string)]
    is_active: Optional[bool] = True
    timer_in_minutes: int # on client side we will request in minutes afterwards convert in seconds

    timer_to_notify_in_seconds: int = 0

    @model_validator(mode='after')
    def convert_minutes_to_seconds(self) -> 'HabitCreate':
        """Converts minutes from input to seconds for internal use."""
        self.timer_to_notify_in_seconds = self.timer_in_minutes * 60
        return self


class HabitUpdate(BaseModel):
    name: Optional[Annotated[str, BeforeValidator(strip_string)]] = None
    is_active: Optional[bool] = None
    timer_to_notify_in_seconds: Optional[int] = None


class HabitCreateBot(BaseModel):
    name: Annotated[str, BeforeValidator(strip_string)]
    timer_to_notify_in_seconds: int
    telegram_chat_id: int


class HabitDeleteBot(BaseModel):
    telegram_chat_id: int