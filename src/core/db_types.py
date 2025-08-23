from datetime import datetime
from typing import Annotated
from sqlalchemy import DateTime, String
from sqlalchemy.orm import mapped_column

# Alias - Primary Key
pk = Annotated[int, mapped_column(primary_key=True)]

# Aliases - Str
str_50 = Annotated[str, mapped_column(String(50))]
str_100 = Annotated[str, mapped_column(String(100))]
str_256 = Annotated[str, mapped_column(String(256))]

# Alias - aware date.
# Tells SQLAlchemy to use a data type that supports time zones in the database.
aware_datetime = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), nullable=False)
]