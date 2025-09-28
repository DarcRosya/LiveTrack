from datetime import datetime
from typing import Annotated, List, Optional
from pydantic import BaseModel, BeforeValidator

from src.models.task import TaskPriority, TaskStatus
from src.utils.validators import strip_string

from .tag_dto import TagRead 

class TaskRead(BaseModel):
    id: int
    title: Annotated[str, BeforeValidator(strip_string)]
    description: str
    status: TaskStatus
    priority: TaskPriority

    deadline: Optional[datetime]
    completed_at: Optional[datetime] 

    tags: List[TagRead] = []

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Optional[Annotated[str, BeforeValidator(strip_string)]] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: Annotated[str, BeforeValidator(strip_string)]
    description: Optional[str] = None

    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    deadline: Optional[datetime] = None 

    class Config:
        from_attributes = True
