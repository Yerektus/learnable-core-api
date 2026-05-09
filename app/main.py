import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_database, init_database
from app.exceptions import setup_exception_handlers
from app.modules.auth.router import router as auth_router
from app.modules.graphs.router import router as graphs_router
from app.modules.users.router import admin_router, router as users_router
from app.modules.kanban.router import router as kanban_router
from app.modules.ai.router import router as ai_router
from app.modules.chats.router import router as chats_router
from app.modules.ai.graph.schema import init_falkordb_schema
from app.modules.ai.graph.embeddings import warmup as warmup_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize MongoDB/Beanie on startup and close Motor on shutdown."""
    logger.info("Starting Learnable Core API")
    await init_database(app)
    # Initialize FalkorDB schema
    init_falkordb_schema()
    # Warmup embedding model (pre-load BGE-M3 to avoid first-request latency)
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warmup_embeddings)
    logger.info("FalkorDB schema initialized, embeddings warmed up")
    try:
        yield
    finally:
        await close_database(app)
        logger.info("Stopped Learnable Core API")


app = FastAPI(
    title="Learnable Core API",
    version="0.1.0",
    description="Authentication and user profile API backed by MongoDB and fastapi-users.",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Registration, JWT login/logout, refresh tokens, email verification, password reset."},
        {"name": "users", "description": "Authenticated and public user profile operations."},
        {"name": "graphs", "description": "Authenticated graph creation and graph management operations."},
        {"name": "chats", "description": "Chat session management and message history."},
        {"name": "admin", "description": "Administrative user operations."},
        {"name": "health", "description": "Service health checks."},
        {"name": "ai", "description": "AI-powered study features: graph generation, chat, materials, planning."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(graphs_router, prefix="/api/v1/graphs", tags=["graphs"])
app.include_router(admin_router, prefix="/api/v1")
app.include_router(kanban_router, prefix="/api/v1/kanban")
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(chats_router, prefix="/api/v1/chats", tags=["chats"])


@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
