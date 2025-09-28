from typing import List, Optional
from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer

from src.api.bot_dependencies import verify_api_key
from src.core.arq_redis import get_arq_redis
from src.core.database import DBSession
from src.models.habit import HabitStatus
from src.models.user import User
from src.queries.habit_queries import habit_repo
from src.queries.user_queries import user_repo
from src.schemas.common_enums import HabitSortBy, SortOrder
from src.schemas.habit_dto import (
    HabitCreateBot,
    HabitDeleteBot,
    HabitRead,
    HabitCreate,
    HabitUpdate,
)
from src.services.auth_services import get_current_user

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/habits",
    tags=["Habits"],
    dependencies=[Depends(http_bearer)],
)

SHOW_LIMIT_MIN = 1
SHOW_LIMIT_MAX = 3


@router.post(
    "",
    response_model=HabitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new habit",
    response_description="Created habit",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Habit could not be created due to a conflict."
        }
    },
)
async def create_habit(
    data: HabitCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
    arq_pool: ArqRedis = Depends(get_arq_redis),
):
    created_habit = await habit_repo.create(
        db=db, 
        user_id=current_user.id, 
        habit_in=data,
        arq_pool=arq_pool,
    )
    if not created_habit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A habit with similar unique properties might already exist.",
        )
    return created_habit


@router.post(
    "/bot/create",
    response_model=HabitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new habit via Telegram Bot",
    dependencies=[Depends(verify_api_key)],
)
async def create_habit_from_bot(
    data: HabitCreateBot, 
    db: DBSession,
    arq_pool: ArqRedis = Depends(get_arq_redis),
):
    user = await user_repo.select_by_telegram_id(db=db, chat_id=data.telegram_chat_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this Telegram ID not found. Please register on the website first."
        )
    
    habit_to_create = HabitCreate(
        name=data.name,
        timer_to_notify_in_seconds=data.timer_to_notify_in_seconds
    )

    created_habit = await habit_repo.create(
        db=db, user_id=user.id, habit_in=habit_to_create, arq_pool=arq_pool
    )
    if not created_habit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A habit with similar unique properties might already exist.",
        )
    return created_habit


@router.get(
    "/{habit_id}",
    response_model=HabitRead,
    summary="Get a single habit of current user",
    responses={404: {"description": "Habit not found."}},
)
async def get_single_habit(
    habit_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    habit = await habit_repo.select_by_id(
        db=db, 
        user_id=current_user.id, 
        habit_id=habit_id
    )
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found."
        )
    return habit


@router.get(
    "",
    response_model=List[HabitRead],
    summary="Get all habits of current user",
    response_description="List of habits",
)
async def get_habits(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    # Add parameters for filtering
    status: Optional[HabitStatus] = Query(default=None, description="Filter by active status (new, active, deactivated)"),
    timer_minutes: Optional[int] = Query(default=None, description="Filter by timer to notify"),
    # Sorting and limit parameters
    sort_by: Optional[HabitSortBy] = Query(default=None, description="Sorting field"),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sorting order"),
    limit: Optional[int] = Query(default=None, ge=SHOW_LIMIT_MIN, le=SHOW_LIMIT_MAX, description="Record limit"),
):
    return await habit_repo.get_multi_for_user(
        db=db,
        user_id=current_user.id,
        status=status,
        timer_minutes=timer_minutes,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit
    )


@router.get(
    "/bot/list/{chat_id}",
    response_model=List[HabitRead],
    summary="Get all habits for a user via Telegram Bot",
    dependencies=[Depends(verify_api_key)],
)
async def get_habits_for_bot(chat_id: int, db: DBSession):
    # Теперь мы делаем один-единственный вызов к новому методу
    habits = await habit_repo.get_multi_for_user_by_telegram_id(
        db=db, chat_id=chat_id, status=HabitStatus.ACTIVE
    )
    # Проверка на существование пользователя больше не нужна,
    # так как если пользователя нет, запрос просто вернет пустой список привычек.
    return habits


@router.patch(
    "/{habit_id}",
    response_model=HabitRead,
    summary="Update a habit by ID",
    response_description="Updated habit",
    responses={404: {"description": "Habit not found."}},
)
async def update_habit(
    habit_id: int,
    habit_to_update_data: HabitUpdate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
    arq_pool: ArqRedis = Depends(get_arq_redis),
):
    updated_habit = await habit_repo.update(
        db=db,
        user_id=current_user.id,
        habit_id=habit_id,
        data_to_update=habit_to_update_data,
        arq_pool=arq_pool,
    )
    if not updated_habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Task not found."
        )
    return updated_habit


@router.delete(
    "/{habit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a habit by ID",
    response_description="Habit deleted",
    responses={404: {"description": "Habit not found."},
               204: {"description": "Habit deleted successfully."}
    }
)
async def delete_habit(
    habit_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user),
    arq_pool: ArqRedis = Depends(get_arq_redis),
):
    was_deleted = await habit_repo.delete(
        db=db,
        user_id=current_user.id,
        habit_id=habit_id,
        arq_pool=arq_pool,
    )
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Habit not found."
        )
    return None


@router.delete(
    "/bot/delete/{habit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a habit via Telegram Bot",
    dependencies=[Depends(verify_api_key)],
)
async def delete_habit_from_bot(
    habit_id: int,
    data: HabitDeleteBot,
    db: DBSession,
    arq_pool: ArqRedis = Depends(get_arq_redis)
):
    user = await user_repo.select_by_telegram_id(db, data.telegram_chat_id)
    if not user:
        raise HTTPException(status_code=404, detail="User with this Telegram ID not found.")

    habit = await habit_repo.select_by_id(db, user_id=user.id, habit_id=habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found or you don't have permission.")

    was_deleted = await habit_repo.delete(
        db=db, user_id=user.id, habit_id=habit_id, arq_pool=arq_pool
    )
    if not was_deleted:
        raise HTTPException(status_code=404, detail="Habit not found.")
    
    return None