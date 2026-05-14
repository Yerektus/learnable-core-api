from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import Strategy

from app.config import get_settings
from app.modules.auth.backend import get_jwt_strategy
from app.modules.auth.dependencies import fastapi_users, get_auth_service, get_user_manager
from app.modules.auth.manager import UserManager
from app.modules.auth.service import AuthService, RefreshTokenRequest, TokenResponse
from app.modules.users.schemas import UserCreate, UserRead

router = APIRouter(tags=["auth"])

router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_reset_password_router())

_REFRESH_COOKIE = "refresh_token"
_REFRESH_PATH = "/api/v1/auth/jwt/refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        max_age=settings.refresh_token_expire_days * 86400,
        path=_REFRESH_PATH,
    )


def _delete_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path=_REFRESH_PATH,
    )


@router.post("/jwt/login", summary="Login and issue JWT tokens")
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    service: AuthService = Depends(get_auth_service),
    strategy: Strategy = Depends(get_jwt_strategy),
) -> JSONResponse:
    user = await service.authenticate(credentials, user_manager)
    await user_manager.on_after_login(user, request, None)
    tokens = await service.create_token_pair(user, strategy)

    response = JSONResponse(
        content={"access_token": tokens.access_token, "token_type": "bearer"}
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return response


@router.post("/jwt/refresh", summary="Refresh access token using httpOnly cookie")
async def refresh_token(
    response: Response,
    cookie_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    # fallback: body field for backward compat with existing clients
    payload: RefreshTokenRequest | None = None,
    service: AuthService = Depends(get_auth_service),
    strategy: Strategy = Depends(get_jwt_strategy),
) -> JSONResponse:
    token = cookie_token or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    tokens = await service.refresh_token(token, strategy)
    resp = JSONResponse(
        content={"access_token": tokens.access_token, "token_type": "bearer"}
    )
    _set_refresh_cookie(resp, tokens.refresh_token)
    return resp


@router.post("/jwt/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout and clear refresh cookie")
async def logout(response: Response) -> Response:
    _delete_refresh_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
