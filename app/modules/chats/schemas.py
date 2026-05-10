from datetime import datetime
from typing import Literal, Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    node_id: Optional[str] = None
    graph_id: Optional[str] = None
    chat_type: Literal["theory", "task", "planning"] = "theory"


class ChatRead(BaseModel):
    id: PydanticObjectId
    node_id: Optional[PydanticObjectId] = None
    graph_id: Optional[PydanticObjectId] = None
    title: str
    chat_type: Literal["theory", "task", "planning"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatMessageRead(BaseModel):
    id: PydanticObjectId
    chat_id: PydanticObjectId
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanningChatRead(BaseModel):
    id: str
    messages: list[ChatMessageRead]
