from fastapi import FastAPI

from app.api.v1.routers import auth, feed, maintenance, posts, users
from app.core.config import get_settings
from app.core.handlers import register_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(feed.router, prefix="/api/v1")
    app.include_router(maintenance.router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
