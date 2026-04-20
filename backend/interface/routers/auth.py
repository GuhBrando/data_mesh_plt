from fastapi import APIRouter, Depends

from backend.domain.entities.user import User
from backend.interface.dependencies import (
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
)
from backend.interface.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from backend.interface.security import get_current_user
from backend.use_cases.auth.login import LoginUseCase
from backend.use_cases.auth.logout import LogoutUseCase
from backend.use_cases.auth.refresh import RefreshUseCase

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    return await use_case.execute(email=body.email, password=body.password)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    use_case: RefreshUseCase = Depends(get_refresh_use_case),
):
    return await use_case.execute(refresh_token=body.refresh_token)


@router.post("/auth/logout", status_code=200)
async def logout(
    body: LogoutRequest,
    use_case: LogoutUseCase = Depends(get_logout_use_case),
    _: User = Depends(get_current_user),
):
    await use_case.execute(refresh_token=body.refresh_token)
    return {"detail": "Successfully logged out"}
