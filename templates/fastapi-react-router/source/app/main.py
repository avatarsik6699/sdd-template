from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.session import close_db, init_db

configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="[PROJECT_NAME]",
    version="0.1.0",
    description="[PROJECT_DESCRIPTION]",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)
app.include_router(api_v1_router)
