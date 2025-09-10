from .auth_routers import router as auth_router
from .user_routers import router as user_router
from .task_routers import router as task_router

def include_routers(app):
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(task_router)
