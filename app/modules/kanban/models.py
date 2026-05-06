from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import (
    Document,
    Insert,
    Replace,
    Save,
    SaveChanges,
    before_event,
    PydanticObjectId,
)
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.users.models import utc_now


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Document):

    owner_id: PydanticObjectId

    title: str = Field(min_length=1, max_length=120)

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    status: TaskStatus = TaskStatus.TODO

    priority: TaskPriority = TaskPriority.MEDIUM

    graph_id: Optional[str] = None

    topic_id: Optional[str] = None

    source: str = "manual"

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
        name = "tasks"

        indexes = [
            IndexModel(
                [("owner_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_tasks_owner_created",
            ),
        ]