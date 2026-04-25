"""Aggregator for all v1 module routers. Imported once by `app.main`."""

from fastapi import APIRouter

from app.core.constants import API_V1_PREFIX
from app.modules.auth.api import router as auth_router
from app.modules.health.api import router as health_router
from app.modules.users.api import router as users_router

api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
