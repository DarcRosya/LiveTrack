from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings

engine = create_async_engine(
    url=settings.db.DATABASE_URL,
    echo=settings.debug_mode, 
    # pool_size=10,  # Можно настроить размер пула, если понадобится
    # max_overflow=20,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# Base class for all our ORM models.
# SQLAlchemy uses it to collect metadata about tables.
class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# Create a type alias for the session dependency.
DBSession = Annotated[AsyncSession, Depends(get_async_session)]