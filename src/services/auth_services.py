from typing import Callable, Coroutine
from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import DBSession
from src.config.email import send_verification_email
from src.models.user import User
from src.queries.user_queries import user_repo
from src.schemas.auth_dto import TokenInfo
from src.schemas.user_dto import UserCreate
from src.security.jwt_tokens import (
    ACCESS_TOKEN_TYPE,
    EMAIL_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_email_token,
    create_refresh_token,
    decode_jwt,
)
from src.api.dependencies import (
    get_current_token_payload,
    validate_token_type,
)

async def register_user(db: AsyncSession, user_in: UserCreate, background_tasks: BackgroundTasks) -> dict:
    existing_user = await user_repo.select_by_username_or_email(db, user_in.username, user_in.email)
    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    user = await user_repo.create(db=db, user_in=user_in)

    token = create_email_token(user)

    background_tasks.add_task(send_verification_email, user.email, token)

    return {"msg": "Registration successful. Please check your email to verify your account."}


async def login_user(user: User) -> TokenInfo:
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token
    )

async def verify_user_email(token: str, db: AsyncSession) -> dict:
    payload = decode_jwt(token)
    
    await validate_token_type(payload, EMAIL_TOKEN_TYPE)

    email = payload["sub"]
    user = await user_repo.select_by_email(db=db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active_account = True
    await db.commit()

    return {"msg": "Email verified successfully"}


async def get_refresh_token(user: User) -> TokenInfo:
    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return TokenInfo(
        access_token=new_access_token,
        refresh_token=new_refresh_token,  
    )


UserLoader = Callable[[DBSession, int], Coroutine[None, None, User | None]]

class UserGetterFromToken:
    def __init__(self, token_type: str, user_loader: UserLoader = user_repo.select_by_id):
        self.token_type = token_type
        self.user_loader = user_loader

    async def __call__(
        self,
        db: DBSession,
        payload: dict = Depends(get_current_token_payload),
    ):
        await validate_token_type(payload=payload, token_type=self.token_type)

        user_id = int(payload.get("sub"))

        user = await self.user_loader(db=db, user_id=user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user

get_current_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)
get_current_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)

get_current_user_with_tasks = UserGetterFromToken(ACCESS_TOKEN_TYPE, user_loader=user_repo.select_with_tasks)
get_current_user_with_habits = UserGetterFromToken(ACCESS_TOKEN_TYPE, user_loader=user_repo.select_with_habits)
get_current_user_with_tags = UserGetterFromToken(ACCESS_TOKEN_TYPE, user_loader=user_repo.select_with_tags)

get_current_user_with_all_data = UserGetterFromToken(ACCESS_TOKEN_TYPE, user_loader=user_repo.select_with_all_relations)
