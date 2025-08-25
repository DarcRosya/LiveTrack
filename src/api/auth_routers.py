from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.services.auth_services import register_user, login_user
from src.models.user import User
from src.schemas.user_dto import UserCreate
from src.schemas.auth_dto import RegisterForm, TokenInfo

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