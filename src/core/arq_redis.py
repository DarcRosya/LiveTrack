import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings as ArqRedisSettings
from src.config.settings import settings

# Global variable for storing the connection pool
arq_redis = None

async def get_arq_redis():
    """Dependency for getting the ARQ client."""
    return arq_redis


async def init_arq_redis():
    """Initialize the ARQ connection pool at application startup."""
    global arq_redis

    arq_redis = await create_pool(
        ArqRedisSettings(
            host=settings.redis.HOST, 
            port=settings.redis.PORT, 
            ssl=True,  # <-- Specify that SSL/TLS should be used
            ssl_ca_certs=settings.redis.SSL_CA_CERTS  # <-- Provide the path to the certificate
        )
    )


async def close_arq_redis():
    """Close the connection pool when stopping the application."""
    await arq_redis.close()
