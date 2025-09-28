from datetime import datetime
from pydantic import BaseModel, BeforeValidator, EmailStr, Field
from src.utils.validators import strip_string
from typing import TYPE_CHECKING, Annotated, Optional

if TYPE_CHECKING: 
    from src.models.user import User


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr

    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: Annotated[str, BeforeValidator(strip_string)]
    email: Annotated[EmailStr, BeforeValidator(strip_string)]
    password: str


class UserUpdate(BaseModel):
    username: Optional[Annotated[str, BeforeValidator(strip_string)]] = None 
    email: Optional[Annotated[EmailStr, BeforeValidator(strip_string)]] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=4, description="New password (minimum 4 symbols)")


class UserLinkTelegram(BaseModel):
    username: Annotated[str, BeforeValidator(strip_string)]
    password: str
    telegram_chat_id: int