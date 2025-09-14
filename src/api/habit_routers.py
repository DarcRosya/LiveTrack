from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer

from src.core.database import DBSession
from src.models.habit import HabitStatus
from src.models.user import User
from src.queries.habit_queries import habit_repo
from src.schemas.common_enums import HabitSortBy, SortOrder
from src.schemas.habit_dto import (
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
    current_user: User = Depends(get_current_user)
):
    created_habit = await habit_repo.create(
        db=db, 
        user_id=current_user.id, 
        habit_in=data
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
):
    updated_habit = await habit_repo.update(
        db=db,
        user_id=current_user.id,
        habit_id=habit_id,
        data_to_update=habit_to_update_data
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
):
    was_deleted = await habit_repo.delete(
        db=db,
        user_id=current_user.id,
        habit_id=habit_id,
    )
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Habit not found."
        )
    return None