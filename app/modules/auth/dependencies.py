from collections.abc import AsyncGenerator

from beanie import PydanticObjectId
from fastapi import Depends
from fastapi_users import FastAPIUsers

from app.modules.auth.backend import get_auth_backend
from app.modules.auth.manager import UserManager
from app.modules.auth.service import AuthService
from app.modules.users.dependencies import get_user_repository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


async def get_user_manager(
    repo: UserRepository = Depends(get_user_repository),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(repo)


fastapi_users = FastAPIUsers[User, PydanticObjectId](get_user_manager, [get_auth_backend()])
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repo)


async def current_admin_user(
    user: User = Depends(current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> User:
    return await service.require_admin(user)
