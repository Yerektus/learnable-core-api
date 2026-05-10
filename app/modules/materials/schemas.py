from datetime import datetime
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict


class MaterialListItem(BaseModel):
    id: PydanticObjectId
    node_id: PydanticObjectId
    type: Literal["notes", "cards"]
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialDetail(BaseModel):
    id: PydanticObjectId
    node_id: PydanticObjectId
    type: Literal["notes", "cards"]
    title: str
    content: str
    cards: list[dict[str, str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
