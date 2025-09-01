from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from .tag_dto import TagRead 

class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str

    deadline: Optional[datetime] = None 
    completed_at: Optional[datetime] = None

    tags: List[TagRead] = []

    class Config:
        from_attributes = True