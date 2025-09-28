from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.config.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Проверяет, что API-ключ, переданный в заголовке, верный."""
    if api_key != settings.INTERNAL_API_KEY.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )