from typing import Annotated
from pydantic import BaseModel, BeforeValidator, EmailStr

from src.utils.validators import strip_string


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    

class RegisterForm(BaseModel):
    username: Annotated[str, BeforeValidator(strip_string)]
    email: Annotated[EmailStr, BeforeValidator(strip_string)]
    password: str