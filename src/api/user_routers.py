from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer

from src.core.database import DBSession
from src.services.auth_services import (
    get_current_user,
    get_current_user_with_tasks,
    get_current_user_with_habits,
    get_current_user_with_tags,
)
from src.models.user import User
from src.schemas.habit_dto import HabitRead
from src.schemas.tag_dto import TagRead
from src.schemas.task_dto import TaskRead
from src.schemas.user_dto import (
    PasswordChange, 
    UserRead, 
    UserUpdate
)
from src.queries.user_queries import user_repo
from src.services.user_sevices import change_user_password

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/users",    
    tags=["Users"],
    dependencies=[Depends(http_bearer)],
)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user info",
    response_description="Current user data"
)
async def get_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get(
    "/me/tasks",
    response_model=List[TaskRead],
    summary="Get tasks of current user",
    response_description="List of tasks belonging to the current user"
)
async def get_user_tasks(
    current_user: User = Depends(get_current_user_with_tasks),
):
    return current_user.tasks


@router.get(
    "/me/habits",
    response_model=List[HabitRead],
    summary="Get habits of current user",
    response_description="List of habits belonging to the current user"
)
async def get_user_habits(
    current_user: User = Depends(get_current_user_with_habits),
):
    return current_user.habits


@router.get(
    "/me/tags",
    response_model=List[TagRead],
    summary="Get tags of current user",
    response_description="List of tags belonging to the current user"
)
async def get_user_tags(
    current_user: User = Depends(get_current_user_with_tags),
):
    return current_user.tags


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current use (name, email)",
    response_description="Updated user object",
    responses={404: {"description": "User not found"}}
)
async def update_my_profile(
    user_update_data: UserUpdate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    updated_user = await user_repo.update(
        db=db, user_to_update=current_user, new_data=user_update_data
    )
    return updated_user


@router.patch(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user's password",
)
async def change_my_password(
    password_data: PasswordChange,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    await change_user_password(
        db=db, user_to_update=current_user, password_data=password_data
    )
    # If the password change is successful, no data needs to be returned,
    # a 204 No Content status is sufficient.
    return None


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the current user's account",
    responses={
        401: {"description": "Authentication required"},
    }
)
async def delete_user_account(
    db: DBSession,
    current_user: User = Depends(get_current_user),
):

    await user_repo.delete(db=db, user_to_delete=current_user)
    return None