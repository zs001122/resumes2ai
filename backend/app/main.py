from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router
from app.core.config import settings
from app.core.runtime import ensure_runtime_dirs


def create_app() -> FastAPI:
    ensure_runtime_dirs()

    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(health_router, prefix="/api")
    app.include_router(ai_router, prefix="/api")
    app.include_router(jobs_router, prefix="/api")
    app.include_router(resumes_router, prefix="/api")

    return app


app = create_app()
