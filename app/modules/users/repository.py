from beanie import PydanticObjectId
from fastapi_users_db_beanie import BeanieUserDatabase

from app.modules.users.models import User


class UserRepository:

    def __init__(self) -> None:
        self.user_db = BeanieUserDatabase(User)

    async def get_by_id(self, user_id: PydanticObjectId | str) -> User | None:
        try:
            object_id = PydanticObjectId(user_id)
        except (TypeError, ValueError):
            return None
        return await User.get(object_id)

    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

    async def get_by_username(self, username: str) -> User | None:
        return await User.find_one(User.username == username)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return await User.find_all().sort("-created_at").skip(skip).limit(limit).to_list()

    async def create(self, data: dict) -> User:
        user = User(**data)
        return await user.insert()

    async def update(self, user: User, data: dict) -> User:
        for field, value in data.items():
            setattr(user, field, value)
        return await user.save()

    async def delete(self, user: User) -> None:
        await user.delete()
