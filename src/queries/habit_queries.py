import logging
from typing import List, Optional
from datetime import timedelta

from sqlalchemy import and_, select, update, delete as delete_query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from src.models import User, Habit
from src.models.habit import HabitStatus
from src.schemas.common_enums import HabitSortBy, SortOrder
from src.schemas.habit_dto import HabitCreate, HabitUpdate


class HabitRepository:
    """
    Repository for all database operations with the Habit model.
    Encapsulates all database query logic.
    """

    # --- CREATION METHODS ---

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        habit_in: HabitCreate,
        arq_pool: ArqRedis
    ) -> Habit | None:
        """Creates a new habit and schedules the first notification job if active."""
        habit_data = habit_in.model_dump(exclude={'timer_in_minutes'})
        db_habit = Habit(**habit_data, user_id=user_id)
        
        try:
            db.add(db_habit)
            await db.flush()  # Assigns an ID to db_habit without committing

            if db_habit.is_active:
                job = await arq_pool.enqueue_job(
                    'send_habit_notification',
                    db_habit.id,
                    _defer_by=timedelta(seconds=db_habit.timer_to_notify_in_seconds)
                )
                db_habit.job_id = job.job_id
            
            await db.commit()
            await db.refresh(db_habit)
            return db_habit
        
        except IntegrityError:
            await db.rollback()
            logging.warning(f"IntegrityError on creating habit for user {user_id}.")
            return None

    # --- READING METHODS (GET) ---

    async def select_by_id(self, db: AsyncSession, user_id: int, habit_id: int) -> Habit | None:
        """Retrieves a single habit by its ID, ensuring it belongs to the user."""
        query = select(Habit).filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        status: Optional[HabitStatus] = None,
        timer_minutes: Optional[int] = None,
        sort_by: Optional[HabitSortBy] = None,
        sort_order: SortOrder = SortOrder.DESC,
        limit: Optional[int] = None,
    ) -> List[Habit]:
        """Retrieves a list of habits for a user with optional filtering and sorting."""
        query = select(Habit).filter(Habit.user_id == user_id)

        # Apply filters
        if status is not None:
            if status == HabitStatus.DEACTIVATED:
                query = query.filter(Habit.is_active == False)
            elif status == HabitStatus.ACTIVE:
                query = query.filter(Habit.is_active == True)

        if timer_minutes is not None:
            timer_seconds = timer_minutes * 60
            query = query.filter(Habit.timer_to_notify_in_seconds == timer_seconds)

        # Apply sorting
        if sort_by:
            sort_column = getattr(Habit, sort_by.value, None)
            if sort_column is not None:
                query = query.order_by(sort_column.desc() if sort_order == SortOrder.DESC else sort_column.asc())
        else:
            query = query.order_by(Habit.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_multi_for_user_by_telegram_id(
        self, 
        db: AsyncSession, 
        chat_id: int,
        status: HabitStatus = HabitStatus.ACTIVE
    ) -> List[Habit]:
        """Retrieves a list of habits for a user via their telegram_chat_id using a single JOIN query."""
        query = (
            select(Habit)
            .join(User)
            .filter(User.telegram_chat_id == chat_id)
        )

        if status == HabitStatus.DEACTIVATED:
            query = query.filter(Habit.is_active == False)
        elif status == HabitStatus.ACTIVE:
            query = query.filter(Habit.is_active == True)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    # --- UPDATE METHODS ---

    async def update(
        self, 
        db: AsyncSession, 
        user_id: int, 
        habit_id: int, 
        data_to_update: HabitUpdate, 
        arq_pool: ArqRedis
    ) -> Habit | None:
        """Updates a habit and manages its notification job based on status changes."""
        data = data_to_update.model_dump(exclude_unset=True)
        if not data:
            return await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)

        habit_before_update = await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)
        if not habit_before_update:
            return None
        
        was_active_before = habit_before_update.is_active
        job_id_before = habit_before_update.job_id

        query = (
            update(Habit)
            .filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
            .values(**data)
            .returning(Habit)
        )
        result = await db.execute(query)
        habit_after_update = result.scalar_one_or_none()

        if habit_after_update:
            # Case 1: Habit is reactivated
            if not was_active_before and habit_after_update.is_active:
                logging.info(f"Habit '{habit_after_update.name}' reactivated. Scheduling job.")
                job = await arq_pool.enqueue_job(
                    'send_habit_notification', 
                    habit_after_update.id,   
                    _defer_by=timedelta(seconds=habit_after_update.timer_to_notify_in_seconds)
                )
                habit_after_update.job_id = job.job_id
            
            # Case 2: Habit is deactivated
            elif was_active_before and not habit_after_update.is_active and job_id_before:
                logging.info(f"Habit '{habit_after_update.name}' deactivated. Aborting job {job_id_before}.")
                try:
                    await arq_pool.abort_job(job_id_before)
                    habit_after_update.job_id = None
                except Exception as e:
                    logging.error(f"Failed to abort job {job_id_before}: {e}")
            
            await db.commit()

        return habit_after_update

    # --- DELETION METHODS ---

    async def delete(self, db: AsyncSession, user_id: int, habit_id: int, arq_pool: ArqRedis) -> bool:
        """Deletes a habit and aborts its scheduled notification job."""
        habit_to_delete = await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)
        if not habit_to_delete:
            return False
        
        if habit_to_delete.job_id:
            try:
                logging.info(f"Deleting habit, aborting job {habit_to_delete.job_id}")
                await arq_pool.abort_job(habit_to_delete.job_id)
            except Exception as e:
                logging.error(f"Could not abort job {habit_to_delete.job_id} during habit deletion: {e}")

        query = delete_query(Habit).filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
        result = await db.execute(query)
        await db.commit()

        return result.rowcount > 0


habit_repo = HabitRepository()