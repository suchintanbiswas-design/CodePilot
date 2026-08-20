from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.database import close_db, get_db, init_db
from app.config.logging import setup_logging
from app.config.redis import close_redis, get_redis, init_redis
from app.config.settings import settings
from app.middleware.error_handler import global_error_handler, validation_error_handler
from app.middleware.security import SecurityHeadersMiddleware
from app.routes import api_router
from app.utils.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    await init_redis()
    yield
    await close_db()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_exception_handler(AppException, global_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, global_error_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "error"
    redis_status = "error"

    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            db_status = "ok"
            break
    except Exception:
        pass

    try:
        redis_client = await get_redis()
        if redis_client and await redis_client.ping():
            redis_status = "ok"
    except Exception:
        pass

    return {
        "status": "healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        "checks": {
            "database": db_status,
            "redis": redis_status
        },
        "version": "1.0.0"
    }

@app.get("/ready", tags=["Health"])
async def readiness_check():
    health = await health_check()
    if health["status"] == "healthy":
        return health
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail="Service Unavailable")
