import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings as ArqRedisSettings
from src.config.settings import settings

# Глобальная переменная для хранения пула соединений
arq_redis = None

async def get_arq_redis():
    """Зависимость для получения клиента ARQ."""
    return arq_redis


async def init_arq_redis():
    """Инициализация пула соединений ARQ при старте приложения."""
    global arq_redis

    arq_redis = await create_pool(
        ArqRedisSettings(
            host=settings.redis.HOST, 
            port=settings.redis.PORT, 
            ssl=True,  # <-- Говорим, что нужно использовать SSL/TLS
            ssl_ca_certs=settings.redis.SSL_CA_CERTS # <-- И указываем путь к сертификату
        )
    )


async def close_arq_redis():
    """Закрытие пула соединений при остановке приложения."""
    await arq_redis.close()