from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from src.models.user import User


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr

    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str