import sys
import logging
from datetime import timedelta
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from arq.connections import RedisSettings as ArqRedisSettings

from src.core.database import async_session_factory
from src.models import Habit
from src.config.settings import settings
from src.services.telegram_sender import send_message

# --- Configuration ---
MAX_TRIES = 3
RETRY_DELAY_SECONDS = 15

# --- Logging Setup ---
# This basic config is great for a standalone worker process.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


async def send_habit_notification(ctx, habit_id: int, *, job_try: int = 1):
    """
    Sends a habit notification via Telegram and reschedules the next one.
    Implements a manual retry mechanism in case of transient errors.
    """
    arq_pool = ctx['redis']
    
    try:
        async with async_session_factory() as db:
            logging.info(f"Attempt #{job_try}/{MAX_TRIES} for habit ID: {habit_id}")

            # Eagerly load the related user to avoid extra queries
            query = select(Habit).options(selectinload(Habit.user)).filter(Habit.id == habit_id)
            result = await db.execute(query)
            habit = result.scalar_one_or_none()

            # Check if the habit and its user are valid for notification
            if not (habit and habit.is_active and habit.user and habit.user.telegram_chat_id):
                logging.warning(f"Habit ID: {habit_id} is inactive or user has no chat_id. Stopping notifications.")
                return "Notification stopped."

            # Send notification via the Telegram service
            notification_message = f" Heeeey!!!😊 Time to '{habit.name}'!\n \
            Take care and not forget that after {habit.timer_to_notify_in_seconds} I will text you again😘🤪" 

            await send_message(
                chat_id=habit.user.telegram_chat_id, 
                text=notification_message
            )
            
            # Reschedule the next job in the cycle
            next_job = await arq_pool.enqueue_job(
                'send_habit_notification', 
                habit.id, 
                _defer_by=timedelta(seconds=habit.timer_to_notify_in_seconds)
            )
            
            # Update the job_id in the DB to track the *next* scheduled job
            stmt = update(Habit).where(Habit.id == habit_id).values(job_id=next_job.job_id)
            await db.execute(stmt)
            await db.commit()
            logging.info(f"Habit ID: {habit_id}. Next job scheduled with ID: {next_job.job_id}")

    except Exception as e:
        logging.error(f"Error in task for habit ID: {habit_id} (attempt {job_try}): {e}")
        
        # Manual retry logic
        if job_try < MAX_TRIES:
            logging.warning(f"Rescheduling task for habit ID: {habit_id} in {RETRY_DELAY_SECONDS}s.")
            await arq_pool.enqueue_job(
                'send_habit_notification',
                habit_id,
                _defer_by=timedelta(seconds=RETRY_DELAY_SECONDS),
                job_try=job_try + 1
            )
        else:
            logging.error(f"All {MAX_TRIES} attempts for habit ID: {habit_id} have failed. Giving up.")

    return "Notification processed."


class WorkerSettings:
    """
    Configuration class for the ARQ worker.
    Defines which functions the worker can execute and how it connects to Redis.
    """

    functions = [send_habit_notification]
    
    # Connection settings for the worker's Redis client, including TLS
    redis_settings = ArqRedisSettings(
        host=settings.redis.HOST,
        port=settings.redis.PORT,
        ssl=True,
        ssl_ca_certs=settings.redis.SSL_CA_CERTS
    )
