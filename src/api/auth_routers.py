from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.models.user import User
from src.schemas.user_dto import UserCreate
from src.schemas.auth_dto import RegisterForm, TokenInfo
from src.services.auth_services import (
    register_user, 
    login_user, 
    verify_user_email,
    get_current_user_for_refresh,
    get_refresh_token,
)

from .dependencies import validate_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
async def register(
    background_tasks: BackgroundTasks,
    form_data: RegisterForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user_in = UserCreate(
        username=form_data.username,
        email=form_data.email,
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
