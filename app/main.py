import asyncio
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
from app.modules.materials.router import router as materials_router
from app.modules.ai.graph.schema import init_falkordb_schema
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize MongoDB/Beanie on startup and close Motor on shutdown."""
    logger.info("Starting Learnable Core API")
    await init_database(app)

    # Run FalkorDB init in a thread — it uses synchronous Redis I/O that would
    # block the event loop and cause Railway health-check timeouts if run inline.
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, init_falkordb_schema)
        logger.info("FalkorDB schema initialized")
    except Exception:
        logger.exception("FalkorDB schema init failed — continuing without graph indexes")

    # Pre-generate and cache the OpenAPI schema so the first /docs request is
    # instant and any schema errors surface in startup logs (visible in Railway).
    try:
        schema = app.openapi()
        logger.info("OpenAPI schema pre-generated OK (%d paths)", len(schema.get("paths", {})))
    except Exception:
        logger.exception("OpenAPI schema generation FAILED — /docs will be unavailable")

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
        {"name": "materials", "description": "Saved AI-generated study materials (notes and flashcards) per node."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

setup_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(graphs_router, prefix="/api/v1/graphs", tags=["graphs"])
app.include_router(admin_router, prefix="/api/v1")
app.include_router(kanban_router, prefix="/api/v1/kanban")
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(chats_router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(materials_router, prefix="/api/v1/materials", tags=["materials"])


@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
