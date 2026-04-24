import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.db.session import close_db, init_db

ROUTER_V1_PREFIX = "/api/v1"

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
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


@app.middleware("http")
async def add_request_id(request: Request, call_next: Any) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health_router, prefix=ROUTER_V1_PREFIX)
app.include_router(auth_router, prefix=ROUTER_V1_PREFIX)
