from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from src.config.settings import settings
from src.api import include_routers
from src.core.arq_redis import init_arq_redis, close_arq_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Приложение запускается ---")
    await init_arq_redis() # <-- Инициализируем ARQ
    yield
    print("--- Приложение останавливается ---")
    await close_arq_redis() # <-- Закрываем соединения

# Создаем экземпляр FastAPI
app = FastAPI(
    title=settings.run.PROJECT_NAME, # <-- Теперь берем из AppSettings
    description="Real-Time Task & Habit Tracker (API)",
    version="0.5.1",
    docs_url="/docs" if settings.debug_mode else None,
    redoc_url="/redoc" if settings.debug_mode else None,
    lifespan=lifespan
)

include_routers(app)

# Health check endpoint
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": f"Welcome to {settings.run.PROJECT_NAME} API!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# poetry run uvicorn src.main:app --reload

# poetry run arq src.core.worker.WorkerSettings