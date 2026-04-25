"""Users module — public API.

Cross-module imports MUST go through this package
(`from app.modules.users import ...`). Reaching into submodules
(`app.modules.users.repository`, `.models`, `.utils`) from outside the module is
forbidden by convention.
"""

from app.modules.users.dependencies import get_user_repository, get_user_service
from app.modules.users.exceptions import EmailAlreadyExists, UserNotFound
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserOut
from app.modules.users.service import UserService

__all__ = [
    "EmailAlreadyExists",
    "User",
    "UserCreate",
    "UserNotFound",
    "UserOut",
    "UserRepository",
    "UserRole",
    "UserService",
    "get_user_repository",
    "get_user_service",
]
