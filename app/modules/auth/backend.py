from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from app.config import get_settings


def get_jwt_strategy() -> JWTStrategy:
    settings = get_settings()
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        algorithm=settings.algorithm,
    )


def get_auth_backend() -> AuthenticationBackend:
    return AuthenticationBackend(
        name="jwt",
        transport=BearerTransport(tokenUrl="/api/v1/auth/jwt/login"),
        get_strategy=get_jwt_strategy,
    )
