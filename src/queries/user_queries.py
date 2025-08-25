from fastapi import HTTPException
from sqlalchemy import or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user_dto import UserCreate
from src.security.password_hashing import hash_password


async def create_user_query(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        hash_password=hash_password(user_in.password),
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


async def select_user_by_username(db: AsyncSession, username: str) -> User | None:
    query = (
        select(User)
        .filter(User.username == username)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def select_user_by_username_or_email(db: AsyncSession, username: str, email: str) -> User | None:
    query = (
        select(User)
        .filter(
            or_(User.username == username, User.email == email)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()