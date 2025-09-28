from typing import List, Optional
from sqlalchemy import and_, select, update, delete as delete_query
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, Task, Tag
from src.models.task import TaskPriority, TaskStatus
from src.schemas.common_enums import SortOrder, TaskSortBy
from src.schemas.task_dto import TaskCreate, TaskUpdate
from src.utils.date_handling import make_aware, normalize_dates 


class TaskRepository:
    """
    Repository for all database operations with the __TASK__ model.
    Encapsulates all database query logic.
    """

    # --- CREATION METHODS ---

    async def create(self, db: AsyncSession, user_id: int, task_in: TaskCreate) -> Task | None:
        """Creates a new task for the specified user."""
        task_data = task_in.model_dump()
        if "deadline" in task_data and task_data["deadline"] is not None:
            task_data["deadline"] = make_aware(task_data["deadline"])

        db_task = Task(**task_data, user_id=user_id)
        
        try:
            db.add(db_task)
            await db.commit()
            await db.refresh(db_task)
            # A fresh select is used to correctly load relationships like tags
            return await self.select_by_id(db=db, user_id=user_id, task_id=db_task.id)
        except IntegrityError:
            await db.rollback()
            return None

    # --- READING METHODS (GET) ---

    async def select_by_id(self, db: AsyncSession, user_id: int, task_id: int) -> Task | None:
        """Retrieves a single task by its ID, ensuring it belongs to the user and loading its tags."""
        query = (
            select(Task)
            .filter(and_(Task.id == task_id, Task.user_id == user_id))
            .options(selectinload(Task.tags))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: Optional[TaskSortBy] = None,
        sort_order: SortOrder = SortOrder.DESC,
        limit: Optional[int] = None,
    ) -> List[Task]:
        """Retrieves a list of tasks for a user with optional filtering, sorting, and eager-loaded tags."""
        query = select(Task).filter(Task.user_id == user_id).options(selectinload(Task.tags))

        # Apply filters
        if status is not None:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if tag_ids:
            query = query.filter(Task.tags.any(Tag.id.in_(tag_ids)))

        # Apply sorting
        if sort_by:
            sort_column = getattr(Task, sort_by.value, None)
            if sort_column is not None:
                query = query.order_by(sort_column.desc() if sort_order == SortOrder.DESC else sort_column.asc())
        else:
            query = query.order_by(Task.created_at.desc())

        # Apply limit
        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    # --- UPDATE METHODS ---

    async def update(
        self, 
        db: AsyncSession,
        user_id: int, 
        task_id: int, 
        data_to_update: TaskUpdate
    ) -> Task | None:
        """Updates a task belonging to the specified user."""
        updated_data = data_to_update.model_dump(exclude_unset=True)
        if not updated_data:
            return await self.select_by_id(db=db, user_id=user_id, task_id=task_id)
        
        updated_data = normalize_dates(updated_data, ["deadline", "completed_at"])

        query = (
            update(Task)
            .filter(and_(Task.id == task_id, Task.user_id == user_id))
            .values(**updated_data)
        )
        result = await db.execute(query)

        if result.rowcount == 0:
            return None # Task not found or does not belong to the user

        await db.commit()
        return await self.select_by_id(db=db, user_id=user_id, task_id=task_id)

    # --- DELETION METHODS ---

    async def delete(self, db: AsyncSession, user_id: int, task_id: int) -> bool:
        """Deletes a task belonging to the user. Returns True if successful."""
        query = delete_query(Task).filter(and_(Task.id == task_id, Task.user_id == user_id))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


task_repo = TaskRepository()