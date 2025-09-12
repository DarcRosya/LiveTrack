from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer

from src.core.database import DBSession
from src.models.task import TaskPriority, TaskStatus
from src.schemas.common_enums import SortOrder, TaskSortBy
from src.services.auth_services import get_current_user
from src.queries.task_queries import task_repo
from src.models.user import User
from src.schemas.task_dto import TaskCreate, TaskRead, TaskUpdate

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(http_bearer)],
)

SHOW_LIMIT_MIN = 1
SHOW_LIMIT_MAX = 3

@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    response_description="Created task",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Task could not be created due to a conflict."
        }
    },
)
async def create_task(
    data: TaskCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    create_task = await task_repo.create(
        db=db, 
        user_id=current_user.id, 
        task_in=data
    )
    if not create_task:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A task with similar unique properties might already exist.",
        )
    return create_task


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get a single task by its ID",
    responses={404: {"description": "Task not found."}}
)
async def get_single_task(
    task_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    task = await task_repo.select_by_id(
        db=db, 
        task_id=task_id, 
        user_id=current_user.id
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    return task


@router.get(
    "",
    response_model=List[TaskRead],
    summary="Get all tasks of current user",
    response_description="List of tasks",
)
async def get_tasks(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    # Add parameters for filtering
    status: Optional[TaskStatus] = Query(default=None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(default=None, description="Filter by priority"),
    tag_ids: Optional[List[int]] = Query(
        default=None,
        description="List of ID tags for filtering tasks (multiple tags can be specified)"
    ),
    # Sorting and limit parameters
    sort_by: Optional[TaskSortBy] = Query(default=None, description="Sorting field"),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sorting order"),
    limit: Optional[int] = Query(default=None, ge=SHOW_LIMIT_MIN, le=SHOW_LIMIT_MAX, description="Record limit"),
):
    return await task_repo.get_multi_for_user(
        db=db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        tag_ids=tag_ids,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit
    )


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update a task by ID",
    response_description="Updated task",
    responses={404: {"description": "Task not found."}}
)
async def update_task(
    task_id: int,
    task_to_update_data: TaskUpdate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    updated_task = await task_repo.update(
        db=db, 
        user_id=current_user.id, 
        task_id=task_id, 
        data_to_update=task_to_update_data
    )
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Task not found."
        )
    return updated_task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task by ID",
    response_description="Task deleted",
    responses={404: {"description": "Task not found."},
               204: {"description": "Task deleted successfully."}
    }
)
async def delete_task(
    task_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)   
):
    was_deleted = await task_repo.delete(
        db=db, 
        user_id=current_user.id, 
        task_id=task_id
    )
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    # If everything went well, FastAPI will automatically return a 204 No Content response,
    # since we specified this in the decorator and are not returning anything.
    return None