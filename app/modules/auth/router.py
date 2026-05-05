from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import Strategy

from app.modules.auth.backend import get_jwt_strategy
from app.modules.auth.dependencies import fastapi_users, get_auth_service, get_user_manager
from app.modules.auth.manager import UserManager
from app.modules.auth.service import AuthService, RefreshTokenRequest, TokenResponse
from app.modules.users.schemas import UserCreate, UserRead

router = APIRouter(tags=["auth"])

router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_reset_password_router())


@router.post("/jwt/login", response_model=TokenResponse, summary="Login and issue JWT tokens")
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    service: AuthService = Depends(get_auth_service),
    strategy: Strategy = Depends(get_jwt_strategy),
) -> TokenResponse:
    user = await service.authenticate(credentials, user_manager)
    await user_manager.on_after_login(user, request, None)
    return await service.create_token_pair(user, strategy)


@router.post("/jwt/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
    strategy: Strategy = Depends(get_jwt_strategy),
) -> TokenResponse:
    return await service.refresh_token(payload.refresh_token, strategy)


@router.post("/jwt/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout current JWT session")
async def logout() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
