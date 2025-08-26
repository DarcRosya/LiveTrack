from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.config.email import send_verification_email
from src.models.user import User
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
    get_user_by_token_sub,
    validate_token_type,
)
from src.queries.user_queries import (
    create_user_query, 
    select_user_by_username_or_email,
    select_user_by_email,
)


async def register_user(db: AsyncSession, user_in: UserCreate, background_tasks: BackgroundTasks) -> dict:
    existing_user = await select_user_by_username_or_email(db, user_in.username, user_in.email)
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
    user = await create_user_query(db=db, user_in=user_in)

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
    user = await select_user_by_email(db=db, email=email)
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


class UserGetterFromToken:
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(
        self,
        payload: dict = Depends(get_current_token_payload),
        db: AsyncSession = Depends(get_async_session),
    ):
        await validate_token_type(payload=payload, token_type=self.token_type)
        return await get_user_by_token_sub(payload=payload, db=db)
    

get_current_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)
get_current_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)
