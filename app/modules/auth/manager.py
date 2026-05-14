import logging

from beanie import PydanticObjectId
from fastapi import HTTPException, Request, status
from fastapi_users import BaseUserManager, InvalidPasswordException
from fastapi_users_db_beanie import ObjectIDIDMixin
from fastapi_users.password import PasswordHelper
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate

logger = logging.getLogger(__name__)


def get_password_helper() -> PasswordHelper:
    return PasswordHelper(PasswordHash((BcryptHasher(),)))


class UserManager(ObjectIDIDMixin, BaseUserManager[User, PydanticObjectId]):

    def __init__(self, repo: UserRepository):
        settings = get_settings()
        self.repo = repo
        self.reset_password_token_secret = settings.secret_key
        self.verification_token_secret = settings.secret_key
        super().__init__(repo.user_db, get_password_helper())

    async def create(self, user_create: UserCreate, safe: bool = False, request: Request | None = None) -> User:
        username = user_create.username.lower()
        existing_user = await self.repo.get_by_username(username)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "REGISTER_USERNAME_ALREADY_EXISTS", "message": "Username already exists"},
            )

        normalized_user = user_create.model_copy(update={"username": username})
        try:
            return await super().create(normalized_user, safe=safe, request=request)
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email or username already exists") from exc

    async def validate_password(self, password: str, user: UserCreate | User) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(reason="Password should be at least 8 characters")
        if user.email and user.email.lower() in password.lower():
            raise InvalidPasswordException(reason="Password should not contain e-mail")

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        logger.info("User registered", extra={"user_id": str(user.id), "email": user.email})

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None) -> None:
        logger.info("Password reset requested", extra={"user_id": str(user.id)})

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None) -> None:
        logger.info("Email verification requested", extra={"user_id": str(user.id)})
