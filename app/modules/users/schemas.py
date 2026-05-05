from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"


class UserRead(BaseModel):

    id: PydanticObjectId
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.CreateUpdateDictModel):

    email: EmailStr
    password: str
    username: str = Field(min_length=3, max_length=30, pattern=USERNAME_PATTERN)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()


class UserUpdate(BaseModel):

    username: Optional[str] = Field(default=None, min_length=3, max_length=30, pattern=USERNAME_PATTERN)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value is not None else value
