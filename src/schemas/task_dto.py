from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from src.models.task import TaskPriority, TaskStatus

from .tag_dto import TagRead 

class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority

    deadline: Optional[datetime]
    completed_at: Optional[datetime] 

    tags: List[TagRead] = []

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    deadline: Optional[datetime] = None 

    class Config:
        from_attributes = True
