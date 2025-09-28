from typing import List, Optional
from datetime import timedelta
from sqlalchemy import and_, or_, select, update, delete as delete_query
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from src.models import User, Task, Habit, Tag
from src.models.habit import HabitStatus
from src.schemas.common_enums import HabitSortBy, SortOrder
from src.schemas.habit_dto import HabitCreate, HabitUpdate


class HabitRepository:
    """
    Class repository for all operations with the _HABIT_ model in the database.
    Encapsulates all logic for database queries.
    """
    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        habit_in: HabitCreate,
        arq_pool: ArqRedis # <-- 2. Добавляем новый параметр
    ) -> Habit | None:
        
        habit_data = habit_in.model_dump()
        db_habit = Habit(**habit_data, user_id=user_id)

        try:
            db.add(db_habit)
            await db.flush()
            
            # --- 3. ВСТАВЛЯЕМ ЛОГИКУ ПЛАНИРОВАНИЯ ЗДЕСЬ ---
            # Если привычка была создана как активная,
            # планируем для нее первое уведомление.
            if db_habit.is_active:
                job = await arq_pool.enqueue_job(
                    'send_habit_notification', # Имя функции в worker.py
                    db_habit.id,               # Аргумент (ID привычки)
                    # _defer_by - отложить выполнение на указанный промежуток
                    _defer_by=timedelta(seconds=db_habit.timer_to_notify_in_seconds)
                )
                db_habit.job_id = job.job_id

            await db.commit()
            await db.refresh(db_habit)
            return db_habit
        
        except IntegrityError:
            await db.rollback()
            return None


    async def select_by_id(self, db: AsyncSession, user_id: int, habit_id: int) -> Habit | None:
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


    async def get_multi_for_user_by_telegram_id(
        self, 
        db: AsyncSession, 
        chat_id: int,
        status: HabitStatus = HabitStatus.ACTIVE
    ) -> List[Habit]:
        """
        Получает список привычек для пользователя по его telegram_chat_id
        с помощью одного JOIN-запроса.
        """
        # Мы выбираем привычки (Habit)
        query = (
            select(Habit)
            # Соединяем их с таблицей пользователей (User)
            .join(User)
            # И фильтруем по полю telegram_chat_id в таблице User
            .filter(User.telegram_chat_id == chat_id)
        )

        if status is not None:
            if status == HabitStatus.DEACTIVATED:
                query = query.filter(Habit.is_active == False)
            elif status == HabitStatus.ACTIVE:
                query = query.filter(Habit.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def update(
            self, 
            db: AsyncSession, 
            user_id: int, 
            habit_id: int, 
            data_to_update: HabitUpdate, 
            arq_pool: ArqRedis
    ) -> Habit | None:
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
            if not was_active_before and habit_after_update.is_active:
                print(f"Привычка '{habit_after_update.name}' была реактивирована. Планируем уведомление.")
                job = await arq_pool.enqueue_job(
                    'send_habit_notification', 
                    habit_after_update.id,   
                    _defer_by=timedelta(seconds=habit_after_update.timer_to_notify_in_seconds)
                )
                habit_after_update.job_id = job.job_id

            elif was_active_before and not habit_after_update.is_active and job_id_before:
                print("Привычка была деактивирована...")
                try:
                    await arq_pool.abort_job(job_id_before)
                    habit_after_update.job_id = None
                except Exception as e:
                    print(f"Не удалось отменить задачу {job_id_before}: {e}")

            await db.commit()

        return habit_after_update


    async def delete(self, db: AsyncSession, user_id: int, habit_id: int, arq_pool: ArqRedis) -> bool:
        habit_to_delete = await self.select_by_id(db=db, user_id=user_id, habit_id=habit_id)
    
        if not habit_to_delete:
            return False
        
        if habit_to_delete.job_id:
            try:
                # Пытаемся отменить задачу в Redis
                print(f"Отменяем задачу с ID: {habit_to_delete.job_id}")
                await arq_pool.abort_job(habit_to_delete.job_id)
            except Exception as e:
                # Логируем ошибку, если задача не найдена (например, уже выполнилась)
                # Но не прерываем удаление самой привычки
                print(f"Не удалось отменить задачу {habit_to_delete.job_id}: {e}")

        # Теперь удаляем саму привычку из БД
        query = (
            delete_query(Habit)
            .filter(and_(Habit.id == habit_id, Habit.user_id == user_id))
        )
        
        result = await db.execute(query)
        await db.commit()

        return result.rowcount > 0


habit_repo = HabitRepository()