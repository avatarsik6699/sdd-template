"""Auth module — public API.

Cross-module imports MUST go through this package
(`from app.modules.auth import ...`). Reaching into submodules
(`app.modules.auth.utils`, `.service`) from outside the module is forbidden by
convention.
"""

from app.modules.auth.dependencies import get_auth_service, get_current_user, require_role
from app.modules.auth.exceptions import (
    AccountDisabled,
    InsufficientRole,
    InvalidCredentials,
    InvalidToken,
    NotAuthenticated,
)
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.auth.utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

__all__ = [
    "AccountDisabled",
    "AuthService",
    "InsufficientRole",
    "InvalidCredentials",
    "InvalidToken",
    "LoginRequest",
    "NotAuthenticated",
    "TokenResponse",
    "create_access_token",
    "decode_access_token",
    "get_auth_service",
    "get_current_user",
    "hash_password",
    "require_role",
    "verify_password",
]
