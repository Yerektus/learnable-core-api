from datetime import datetime
from typing import Literal

from beanie import Document, Insert, PydanticObjectId, Replace, Save, SaveChanges, before_event
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.users.models import utc_now


class Chat(Document):

    user_id: PydanticObjectId
    node_id: PydanticObjectId
    title: str = Field(default="", max_length=200)
    chat_type: Literal["theory", "task"] = Field(default="theory")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @before_event(Insert)
    def set_created_timestamps(self) -> None:
        now = utc_now()
        self.created_at = now
        self.updated_at = now

    @before_event(Replace, Save, SaveChanges)
    def set_updated_timestamp(self) -> None:
        self.updated_at = utc_now()

    class Settings:
        name = "chats"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_chats_user_created"),
            IndexModel([("user_id", ASCENDING), ("node_id", ASCENDING)], name="idx_chats_user_node"),
        ]


class ChatMessage(Document):

    chat_id: PydanticObjectId
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=utc_now)

    @before_event(Insert)
    def set_created_timestamp(self) -> None:
        self.created_at = utc_now()

    class Settings:
        name = "chat_messages"
        indexes = [
            IndexModel([("chat_id", ASCENDING), ("created_at", ASCENDING)], name="idx_messages_chat_created"),
        ]
