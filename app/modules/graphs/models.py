from datetime import datetime
from typing import Optional

from beanie import Document, Insert, PydanticObjectId, Replace, Save, SaveChanges, before_event
from pydantic import Field, field_validator
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.users.models import utc_now


class Graph(Document):

    owner_id: PydanticObjectId
    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=500)
    custom_prompt: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Graph name cannot be empty")
        return stripped

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @before_event(Insert)
    def set_created_timestamps(self) -> None:
        now = utc_now()
        self.created_at = now
        self.updated_at = now

    @before_event(Replace, Save, SaveChanges)
    def set_updated_timestamp(self) -> None:
        self.updated_at = utc_now()

    class Settings:
        name = "graphs"
        indexes = [
            IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)], name="idx_graphs_owner_created"),
        ]

#ноды которые я добавил     
class GraphNode(Document):

    owner_id: PydanticObjectId

    graph_id: PydanticObjectId

    title: str = Field(min_length=1, max_length=120)

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    position_x: float = 0

    position_y: float = 0

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
        name = "graph_nodes"

        indexes = [
            IndexModel(
                [("graph_id", ASCENDING)],
                name="idx_nodes_graph",
            ),
        ]