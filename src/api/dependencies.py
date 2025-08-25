from typing import Annotated
from fastapi import Depends, Form, HTTPException, status
from jwt import InvalidTokenError, PyJWTError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from asyncpg.exceptions import ProgrammingError

from src.core.database import get_async_session
from src.models.user import User
from src.security.jwt_tokens import TOKEN_TYPE_FIELD, decode_jwt
from src.security.password_hashing import verify_password, oauth2_scheme
from src.queries.user_queries import select_user_by_username


async def validate_user(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        user = await select_user_by_username(db=db, username=username)
    except ProgrammingError:
        raise HTTPException(status_code=500, detail="Database schema is not initialized")

    if not user or not verify_password(password, user.password_in_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid username or password"
        )

    if not user.is_active_account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


async def get_current_token_payload(
        token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    try:
        payload = decode_jwt(token=token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
        )
    return payload


async def validate_token_type(payload: dict, token_type: str) -> None:
    current_token_type = payload.get(TOKEN_TYPE_FIELD)
    if current_token_type != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type {current_token_type!r} expected {token_type!r}"
        )


async def get_user_by_token_sub(payload: dict, db: AsyncSession) -> User:
    try:
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except (ValueError, PyJWTError):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    result = await db.execute(
        select(User).options(selectinload(User.tasks)).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user