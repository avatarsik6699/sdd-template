from uuid import UUID

from app.modules.users.exceptions import UserNotFound
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class UserService:
    """Use-case layer for the users domain. Returns ORM `User` entities;
    the HTTP layer maps them to `UserOut` before sending."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_by_id(self, user_id: UUID) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return user

    async def get_by_email(self, email: str) -> User:
        user = await self._repository.get_by_email(email)
        if user is None:
            raise UserNotFound()
        return user

    async def find_by_email(self, email: str) -> User | None:
        return await self._repository.get_by_email(email)
