from typing import List, Optional
from sqlalchemy import and_, or_, select, update, delete as delete_query
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, Task, Habit, Tag
from src.models.habit import HabitStatus
from src.schemas.common_enums import HabitSortBy, SortOrder
from src.schemas.habit_dto import HabitCreate, HabitUpdate


class HabitRepository:
    """
    Class repository for all operations with the _HABIT_ model in the database.
    Encapsulates all logic for database queries.
    """

    async def create(self, db: AsyncSession, user_id: int, habit_in: HabitCreate) -> Habit | None:
        habit_data = habit_in.model_dump()

        db_habit = Habit(**habit_data, user_id=user_id)

        try:
            db.add(db_habit)
            await db.commit()
            await db.refresh(db_habit)
            return db_habit
        except IntegrityError:
            await db.rollback()
            return None


    async def select_by_id(self, db: AsyncSession, user_id: int, habit_id: int) -> Task | None:
        query = (
            select(Habit)
            .filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
        )

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
        """
        Receives a list of habits for the user with the ability to
        sort, filter, and limit.
        """

        query = (select(Habit).filter(Habit.user_id == user_id))

        if status is not None:
            if status == HabitStatus.DEACTIVATED:
                query = query.filter(Habit.is_active == False)
            elif status == HabitStatus.NEW:
                query = query.filter(and_(Habit.is_active, Habit.duration_days < 3))
            elif status == HabitStatus.ACTIVE:
                query = query.filter(and_(Habit.is_active, Habit.duration_days >= 3))

        if timer_minutes is not None:
            timer_seconds = timer_minutes * 60
            query = query.filter(Habit.timer_to_notify_in_seconds == timer_seconds)

        if sort_by:
            sort_column = getattr(Habit, sort_by.value, None)

            if sort_column is not None:
                if sort_order == SortOrder.DESC:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Habit.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all()


    async def update(self, db: AsyncSession, user_id: int, habit_id: int, data_to_update: HabitUpdate) -> Task| None:
        data = data_to_update.model_dump(exclude_unset=True)
        if not data:
            return await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)

        query = (
            update(Habit)
            .filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
            .values(**data)
        )
        result = await db.execute(query)

        if result.rowcount == 0:
            return None
        
        await db.commit()
        return await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)


    async def delete(self, db: AsyncSession, user_id: int, habit_id: int) -> bool:
        query = (
            delete_query(Habit)
            .filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
        )
        
        result = await db.execute(query)
        await db.commit()

        return result.rowcount > 0


habit_repo = HabitRepository()