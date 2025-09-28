from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from src.utils.validators import strip_string


class TagRead(BaseModel):
    id: int
    name: Annotated[str, BeforeValidator(strip_string)]

    class Config:
        from_attributes = True 