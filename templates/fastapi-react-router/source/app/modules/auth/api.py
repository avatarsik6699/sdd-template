from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users import User, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.login(body.email, body.password)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(_current_user: User = Depends(get_current_user)) -> dict[str, str]:
    # Stateless logout. Add a Redis token blacklist here when revocation is needed.
    return {"detail": "Logged out successfully"}
