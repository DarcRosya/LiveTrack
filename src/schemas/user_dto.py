from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import TYPE_CHECKING, Optional

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


class UserUpdate(BaseModel):
    username: Optional[str] = None 
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 4 symbols)")


class UserLinkTelegram(BaseModel):
    username: str
    password: str
    telegram_chat_id: int