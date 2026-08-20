from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.favorites import router as favorites_router
from app.routes.reviews import router as reviews_router
from app.routes.users import router as users_router
from app.routes.notifications import router as notifications_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router)
api_router.include_router(favorites_router)
api_router.include_router(reviews_router)
api_router.include_router(notifications_router)
