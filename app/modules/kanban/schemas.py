from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.kanban.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):

    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    priority: TaskPriority = TaskPriority.MEDIUM
    graph_id: Optional[PydanticObjectId] = None
    topic_id: Optional[PydanticObjectId] = None
    source: str = Field(default="manual", max_length=50)
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Task title cannot be empty")
        return stripped

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            return "manual"
        return stripped


class TaskUpdate(BaseModel):

    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    graph_id: Optional[PydanticObjectId] = None
    topic_id: Optional[PydanticObjectId] = None
    source: Optional[str] = Field(default=None, max_length=50)
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Task title cannot be empty")
        return stripped

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or "manual"


class TaskRead(BaseModel):

    id: PydanticObjectId
    owner_id: PydanticObjectId
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    graph_id: Optional[PydanticObjectId] = None
    topic_id: Optional[PydanticObjectId] = None
    source: str
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    
    model_config = ConfigDict(from_attributes=True)