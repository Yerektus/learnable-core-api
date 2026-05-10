from datetime import datetime
from typing import Literal, Optional

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

    node_type: Literal["lesson", "topic", "cluster", "quiz"] = "lesson"

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    position_x: float = 0

    position_y: float = 0

    color: Optional[str] = Field(default=None, max_length=32)

    size: Optional[float] = None

    accent: Optional[Literal["left", "right"]] = None

    node_ids: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utc_now)

    updated_at: datetime = Field(default_factory=utc_now)

    summary: Optional[str] = Field(default=None, max_length=1000) #добавил поле для краткого содержания узла, которое может быть сгенерировано ИИ на основе описания и других данных узла, чтобы помочь пользователю быстро понять суть узла без необходимости читать полное описание

    falkordb_deadline_id: Optional[str] = None

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


class GraphEdge(Document):

    owner_id: PydanticObjectId

    graph_id: PydanticObjectId

    source_node_id: PydanticObjectId

    target_node_id: PydanticObjectId

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
        name = "graph_edges"

        indexes = [
            IndexModel(
                [("graph_id", ASCENDING)],
                name="idx_edges_graph",
            ),
            IndexModel(
                [
                    ("graph_id", ASCENDING),
                    ("source_node_id", ASCENDING),
                    ("target_node_id", ASCENDING),   #заметил что не хватает индекса для проверки уникальности рёбер, добавил его, чтобы не допустить создания нескольких рёбер между одними и теми же узлами в одном графе
                ],
                unique=True,
                name="idx_edges_unique",
            ),
        ]
