from datetime import datetime
from typing import Literal, Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GraphCreate(BaseModel):

    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=500)

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


class GraphUpdate(BaseModel):

    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
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


class GraphRead(BaseModel):

    id: PydanticObjectId
    owner_id: PydanticObjectId
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

#вот от сюда добавил ноды 
class GraphNodeCreate(BaseModel):

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


class GraphNodeUpdate(BaseModel):

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    position_x: Optional[float] = None

    position_y: Optional[float] = None

    color: Optional[str] = Field(default=None, max_length=32)

    size: Optional[float] = None

    accent: Optional[Literal["left", "right"]] = None

    node_ids: Optional[list[str]] = None


class GraphNodeRead(BaseModel):

    id: PydanticObjectId

    owner_id: PydanticObjectId

    graph_id: PydanticObjectId

    title: str

    node_type: Literal["lesson", "topic", "cluster", "quiz"] = "lesson"

    description: Optional[str]

    position_x: float

    position_y: float

    color: Optional[str] = None

    size: Optional[float] = None

    accent: Optional[Literal["left", "right"]] = None

    node_ids: list[str] = Field(default_factory=list)

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeCreate(BaseModel):

    source_node_id: PydanticObjectId

    target_node_id: PydanticObjectId


class GraphEdgeRead(BaseModel):

    id: PydanticObjectId

    owner_id: PydanticObjectId

    graph_id: PydanticObjectId

    source_node_id: PydanticObjectId

    target_node_id: PydanticObjectId

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
