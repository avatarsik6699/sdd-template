"""Base exception hierarchy. Domain modules subclass `AppException`.

Subclassing `HTTPException` lets FastAPI render the correct status/body without
extra exception handlers — domain code raises typed exceptions, the framework
serialises them.
"""

from fastapi import HTTPException


class AppException(HTTPException):
    status_code: int = 500
    detail: str = "Internal error"
    headers: dict[str, str] | None = None

    def __init__(
        self,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail if detail is not None else self.detail,
            headers=headers if headers is not None else self.headers,
        )
