from datetime import datetime
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    node_id: str


class ChatRead(BaseModel):
    id: PydanticObjectId
    node_id: PydanticObjectId
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    id: PydanticObjectId
    chat_id: PydanticObjectId
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
