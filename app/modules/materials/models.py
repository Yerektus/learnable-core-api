from datetime import datetime
from typing import Literal

from beanie import Document, Insert, PydanticObjectId, before_event
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.users.models import utc_now


class NodeMaterial(Document):

    owner_id: PydanticObjectId
    node_id: PydanticObjectId
    type: Literal["notes", "cards"]
    title: str = Field(max_length=300)
    content: str = Field(default="")
    cards: list[dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    @before_event(Insert)
    def set_created_timestamp(self) -> None:
        self.created_at = utc_now()

    class Settings:
        name = "node_materials"
        indexes = [
            IndexModel(
                [("owner_id", ASCENDING), ("node_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_materials_owner_node_created",
            ),
        ]
