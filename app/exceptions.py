import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
        message = str(exc)
        field = "username" if "username" in message else "email" if "email" in message else "field"
        logger.warning("Duplicate key error", extra={"field": field, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": f"{field} already exists", "field": field},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
