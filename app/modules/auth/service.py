from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import Strategy
from pydantic import BaseModel

from app.config import get_settings
from app.modules.auth.manager import UserManager
from app.modules.users.repository import UserRepository


class TokenResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):

    refresh_token: str


class AuthService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def authenticate(self, credentials: OAuth2PasswordRequestForm, user_manager: UserManager) -> Any:
        """Authenticate login credentials."""
        user = await user_manager.authenticate(credentials)
        if user is None or not user.is_active:
            user_manager.password_helper.hash(credentials.password)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LOGIN_BAD_CREDENTIALS")
        return user

    async def create_token_pair(self, user: Any, strategy: Strategy) -> TokenResponse:
        return TokenResponse(
            access_token=await strategy.write_token(user),
            refresh_token=self.create_refresh_token(user),
        )

    def create_refresh_token(self, user: Any) -> str:
        settings = get_settings()
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(user.id),
            "type": "refresh",
            "role": user.role,
            "exp": now + timedelta(days=settings.refresh_token_expire_days),
            "iat": now,
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    async def get_user_from_refresh_token(self, token: str) -> Any:
        settings = get_settings()
        credentials_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != "refresh":
                raise credentials_error
            user_id = payload.get("sub")
            if not user_id:
                raise credentials_error
        except jwt.PyJWTError as exc:
            raise credentials_error from exc

        user = await self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise credentials_error
        return user

    async def refresh_token(self, token: str, strategy: Strategy) -> TokenResponse:
        user = await self.get_user_from_refresh_token(token)
        return await self.create_token_pair(user, strategy)

    async def require_admin(self, user: Any) -> Any:
        if user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        return user

    async def request_email_verification(self, user: Any) -> None:
        return None

    async def request_password_reset(self, user: Any) -> None:
        return None
