from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.bot_dependencies import verify_api_key
from src.queries.user_queries import user_repo
from src.core.database import DBSession, get_async_session
from src.models.user import User
from src.schemas.user_dto import UserCreate, UserLinkTelegram
from src.schemas.auth_dto import RegisterForm, TokenInfo
from src.services.auth_services import (
    register_user, 
    login_user, 
    verify_user_email,
    get_current_user_for_refresh,
    get_refresh_token,
)

from .dependencies import validate_user

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(http_bearer)],
)


@router.post("/register")
async def register(
    background_tasks: BackgroundTasks,
    form_data: RegisterForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user_in = UserCreate(
        username=form_data.username.strip(),
        email=form_data.email.strip(),
        password=form_data.password,
    )
    return await register_user(db=db, user_in=user_in, background_tasks=background_tasks) 


@router.post("/login", response_model=TokenInfo)
async def login(
    user: User = Depends(validate_user)
):
    return await login_user(user=user)


@router.get("/verify")
async def verify_email(
    token: str, 
    db: AsyncSession = Depends(get_async_session)
):
    return await verify_user_email(token=token, db=db)


@router.post(
    "/refresh", 
    response_model=TokenInfo,
    response_model_exclude_none=True,
)
async def refresh_token(
    current_user: User = Depends(get_current_user_for_refresh),
):
    return await get_refresh_token(user=current_user)


@router.post(
    "/bot/link",
    summary="Link a Telegram account to a user by username and password",
    dependencies=[Depends(verify_api_key)],
)
async def link_telegram_account(data: UserLinkTelegram, db: DBSession):
    user = await user_repo.authenticate_and_link_telegram(
        db=db,
        username=data.username,
        password=data.password,
        telegram_chat_id=data.telegram_chat_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    return {"message": "Telegram account linked successfully"}