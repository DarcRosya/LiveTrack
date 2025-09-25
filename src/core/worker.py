import logging
from datetime import datetime, timedelta
import sys
from sqlalchemy import select, update
from arq.connections import RedisSettings as ArqRedisSettings

from src.core.database import async_session_factory
from src.models import Habit
from src.config.settings import settings

MAX_TRIES = 3


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


async def send_habit_notification(ctx, habit_id: int, *, job_try: int = 1):
    """
    Отправляет напоминание о привычке и планирует следующее, если нужно.
    """
    arq_pool = ctx['redis']
    
    try:
        # Создаем свою собственную сессию БД для каждой задачи
        async with async_session_factory() as db:
            logging.info(f"Попытка #{job_try}/{MAX_TRIES} для привычки ID: {habit_id}")
            
            # Получаем привычку из базы
            result = await db.execute(select(Habit).filter(Habit.id == habit_id))
            habit = result.scalar_one_or_none()

            if habit and habit.is_active:
                # Логика уведомления
                notification_message = f"!!! НАПОМИНАНИЕ: Пора уделить время привычке '{habit.name}' !!!"
                logging.info(notification_message)
                
                # Логика повторного планирования
                next_job = await arq_pool.enqueue_job(
                    'send_habit_notification', 
                    habit.id, 
                    _defer_by=timedelta(seconds=habit.timer_to_notify_in_seconds)
                )
                
                # Обновляем job_id в базе данных на ID новой, только что запланированной задачи
                query = update(Habit).where(Habit.id == habit_id).values(job_id=next_job.job_id)
                await db.execute(query)
                await db.commit()
                logging.info(f"Привычка ID: {habit_id}. Следующая задача запланирована с ID: {next_job.job_id}")
            else:
                logging.warning(f"Привычка ID: {habit_id} не активна или не найдена. Напоминания остановлены.")

    except Exception as e:
        logging.error(f"Ошибка в задаче для привычки ID: {habit_id} (попытка {job_try}): {e}")
        if job_try < MAX_TRIES:
            logging.warning(f"Перепланируем задачу для привычки ID: {habit_id} через 15 секунд.")
            # Мы сами ставим задачу в очередь снова, явно указывая номер следующей попытки
            await arq_pool.enqueue_job(
                'send_habit_notification',
                habit_id,
                _defer_by=timedelta(seconds=15),
                job_try=job_try + 1 # arq автоматически передаст это в ctx
            )
        else:
            logging.error(f"Все {MAX_TRIES} попытки для привычки ID: {habit_id} исчерпаны. Задача провалена.")

    return "Notification processed."


class WorkerSettings:
    """
    Главный класс настроек для воркера ARQ.
    """
    # Список всех функций, которые умеет выполнять воркер
    functions = [send_habit_notification]
    
    # Вместо on_startup/on_shutdown, мы просто указываем настройки Redis.
    # ARQ сам создаст и будет управлять пулом соединений.
    redis_settings = ArqRedisSettings.from_dsn(settings.redis.dsn)
