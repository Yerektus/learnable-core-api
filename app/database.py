from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.modules.graphs.models import Graph
from app.modules.users.models import User


async def init_database(app: FastAPI) -> None:
    settings = get_settings()
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url, uuidRepresentation="standard")
    app.state.mongodb_client = client
    await init_beanie(database=client[settings.database_name], document_models=[User, Graph])


async def close_database(app: FastAPI) -> None:
    client: AsyncIOMotorClient | None = getattr(app.state, "mongodb_client", None)
    if client is not None:
        client.close()
