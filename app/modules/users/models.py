from datetime import UTC, datetime
from typing import Optional

from beanie import Insert, Replace, Save, SaveChanges, before_event
from fastapi_users.db import BeanieBaseUser
from pydantic import Field, field_validator
from pymongo import ASCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(BeanieBaseUser):

    email: str
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(default="user", pattern=r"^(user|admin)$")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()

    @before_event(Insert)
    def set_created_timestamps(self) -> None:
        now = utc_now()
        self.created_at = now
        self.updated_at = now

    @before_event(Replace, Save, SaveChanges)
    def set_updated_timestamp(self) -> None:
        self.updated_at = utc_now()

    class Settings(BeanieBaseUser.Settings):
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True, name="uniq_users_email"),
            IndexModel([("username", ASCENDING)], unique=True, name="uniq_users_username"),
        ]
