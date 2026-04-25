"""Cross-cutting HTTP middleware. Wired into the FastAPI app in `main.py`."""

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.core.constants import REQUEST_ID_HEADER


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
