from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user_dto import UserCreate
from src.security.password_hashing import hash_password


async def create_user_query(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        password_in_hash=hash_password(user_in.password),
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


async def _get_user_by_attribute(db: AsyncSession, attribute: str, value: str | int) -> User | None:
    """Универсальная функция для поиска пользователя по одному атрибуту."""
    query = select(User).filter(getattr(User, attribute) == value)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def select_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await _get_user_by_attribute(db, "id", user_id)

async def select_user_by_username(db: AsyncSession, username: str) -> User | None:
    return await _get_user_by_attribute(db, "username", username)

async def select_user_by_email(db: AsyncSession, email: EmailStr) -> User | None:
    return await _get_user_by_attribute(db, "email", email)


async def select_user_by_username_or_email(db: AsyncSession, username: str, email: str) -> User | None:
    query = (
        select(User)
        .filter(
            or_(User.username == username, User.email == email)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
