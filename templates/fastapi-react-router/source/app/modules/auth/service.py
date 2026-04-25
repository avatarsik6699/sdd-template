from app.modules.auth.constants import JWT_CLAIM_ROLE, JWT_CLAIM_SUBJECT
from app.modules.auth.exceptions import AccountDisabled, InvalidCredentials
from app.modules.auth.schemas import TokenResponse
from app.modules.auth.utils import create_access_token, verify_password
from app.modules.users import UserNotFound, UserService


class AuthService:
    """Authentication use cases. Depends on `users.UserService` (read-only) for
    looking up users — never touches the User repository or model directly."""

    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    async def login(self, email: str, password: str) -> TokenResponse:
        try:
            user = await self._user_service.get_by_email(email)
        except UserNotFound as exc:
            raise InvalidCredentials() from exc

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentials()

        if not user.is_active:
            raise AccountDisabled()

        token = create_access_token(
            {
                JWT_CLAIM_SUBJECT: str(user.id),
                JWT_CLAIM_ROLE: user.role.value,
            }
        )
        return TokenResponse(access_token=token)
