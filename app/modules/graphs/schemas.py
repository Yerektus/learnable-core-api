from datetime import datetime
from typing import Literal, Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GraphCreate(BaseModel):

    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=500)
    custom_prompt: Optional[str] = Field(default=None, max_length=2000)

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
    custom_prompt: Optional[str] = Field(default=None, max_length=2000)

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
    custom_prompt: Optional[str] = None
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

    summary: Optional[str] = Field(default=None, max_length=1000) #добавил поле для краткого содержания узла, которое может быть сгенерировано ИИ на основе описания и других данных узла, чтобы помочь пользователю быстро понять суть узла без необходимости читать полное описание

    falkordb_deadline_id: Optional[str] = None


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

    summary: Optional[str] = Field(default=None, max_length=1000) #добавил поле для краткого содержания узла, которое может быть сгенерировано ИИ на основе описания и других данных узла, чтобы помочь пользователю быстро понять суть узла без необходимости читать полное описание

    falkordb_deadline_id: Optional[str] = None

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

    summary: Optional[str] = None #добавил поле для краткого содержания узла, которое может быть сгенерировано ИИ на основе описания и других данных узла, чтобы помочь пользователю быстро понять суть узла без необходимости читать полное описание

    falkordb_deadline_id: Optional[str] = None


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


class NodeMaterialCreate(BaseModel):

    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    material_type: str = Field(default="note", max_length=50)


class NodeMaterialRead(BaseModel):

    id: PydanticObjectId
    owner_id: PydanticObjectId
    graph_id: PydanticObjectId
    node_id: PydanticObjectId
    title: str
    content: str
    material_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)