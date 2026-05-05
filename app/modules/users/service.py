from typing import Any

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserRead, UserUpdate


class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_current_profile(self, user: Any) -> UserRead:
        return UserRead.model_validate(user)

    async def get_profile(self, username: str) -> UserRead:
        user = await self.repo.get_by_username(username.lower())
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserRead.model_validate(user)

    async def update_profile(self, user: Any, data: UserUpdate) -> UserRead:
        update_data = data.model_dump(exclude_unset=True)
        username = update_data.get("username")

        if username is not None and username != user.username:
            existing_user = await self.repo.get_by_username(username)
            if existing_user is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

        try:
            updated_user = await self.repo.update(user, update_data)
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists") from exc

        return UserRead.model_validate(updated_user)

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[UserRead]:
        users = await self.repo.get_all(skip=skip, limit=limit)
        return [UserRead.model_validate(user) for user in users]

    async def change_role(self, user_id: Any, role: str) -> UserRead:
        if role not in {"user", "admin"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            updated_user = await self.repo.update(user, {"role": role})
        except DuplicateKeyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate user field") from exc

        return UserRead.model_validate(updated_user)
