from fastapi import FastAPI

from src.config.settings import settings
from src.api import include_routers

# Создаем экземпляр FastAPI
app = FastAPI(
    title=settings.run.PROJECT_NAME, # <-- Теперь берем из AppSettings
    description="Real-Time Task & Habit Tracker (API)",
    version="0.4.3",
    docs_url="/docs" if settings.debug_mode else None,
    redoc_url="/redoc" if settings.debug_mode else None,
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

# Команда для запуска из корневой папки проекта:
# poetry run uvicorn src.main:app --reload