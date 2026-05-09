from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.modules.graphs.models import Graph, GraphNode
from app.modules.users.models import User
from app.modules.kanban.models import Task
from app.modules.chats.models import Chat, ChatMessage


async def init_database(app: FastAPI) -> None:
    settings = get_settings()
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url, uuidRepresentation="standard")
    app.state.mongodb_client = client
    await init_beanie(database=client[settings.database_name], document_models=[User, Graph, GraphNode, Task, Chat, ChatMessage])


async def close_database(app: FastAPI) -> None:
    client: AsyncIOMotorClient | None = getattr(app.state, "mongodb_client", None)
    if client is not None:
        client.close()


def _get_mongo_client() -> AsyncIOMotorClient | None:
    return None
