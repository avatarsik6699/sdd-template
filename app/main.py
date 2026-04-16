import logging
import uuid
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import State
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.core.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


# Pure ASGI middleware instead of @app.middleware("http") / BaseHTTPMiddleware.
# BaseHTTPMiddleware wraps call_next in a separate anyio task, which causes
# "Future attached to a different loop" errors when asyncpg connections are
# involved — a known incompatibility. Pure ASGI middleware operates directly
# on the ASGI protocol without spawning extra tasks, eliminating the conflict.
# This is the same pattern used by Starlette's own CORSMiddleware.
class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for key, value in scope.get("headers", []):
            if key.lower() == b"x-request-id":
                request_id = value.decode()
                break
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store on scope["state"] so downstream handlers can access it via request.state.request_id
        if "state" not in scope:
            scope["state"] = State()
        scope["state"].request_id = request_id

        async def send_with_id(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_id)


app = FastAPI(
    title="[PROJECT_NAME]",
    version="0.1.0",
    description="[PROJECT_DESCRIPTION]",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
