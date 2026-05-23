"""FastAPI Application factory module compiling middlewares, lifespan events, and routers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pnetai_chatbot.infrastructure.logging.logging import setup_logging
from pnetai_chatbot.infrastructure.persistence.mongodb.client import (
    get_chat_client,
    get_website_client,
)
from pnetai_chatbot.infrastructure.persistence.qdrant.client import get_qdrant_client
from pnetai_chatbot.interface.api.middleware import AuthMiddleware, RateLimitMiddleware
from pnetai_chatbot.interface.api.router import router as api_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("Initializing PNetAI Chatbot services...")

    # Validate MongoDB Chat client connection
    try:
        chat_client = get_chat_client()
        if await chat_client.ping():
            logger.info("MongoDB Chat database connection is active.")
        else:
            logger.warning("MongoDB Chat database connection is offline.")
    except Exception as e:
        logger.error("Failed to connect to MongoDB Chat client: %s", e)

    # Validate MongoDB Website client connection
    try:
        website_client = get_website_client()
        if await website_client.ping():
            logger.info("MongoDB Website database connection is active.")
        else:
            logger.warning("MongoDB Website database connection is offline.")
    except Exception as e:
        logger.error("Failed to connect to MongoDB Website client: %s", e)

    # Validate Qdrant vector store connection
    try:
        qdrant_manager = get_qdrant_client()
        if await qdrant_manager.ping():
            logger.info("Qdrant Vector Database connection is active.")
        else:
            logger.warning("Qdrant Vector Database connection is offline.")
    except Exception as e:
        logger.error("Failed to connect to Qdrant client: %s", e)

    yield

    logger.info("Shutting down PNetAI Chatbot services...")
    try:
        await get_chat_client().close()
    except Exception as e:
        logger.error("Error closing MongoDB Chat client: %s", e)

    try:
        await get_website_client().close()
    except Exception as e:
        logger.error("Error closing MongoDB Website client: %s", e)

    try:
        await get_qdrant_client().close()
    except Exception as e:
        logger.error("Error closing Qdrant client: %s", e)


def create_app() -> FastAPI:
    """Create, configure, and return the primary FastAPI application instance.

    Returns:
        The fully-configured production FastAPI instance.
    """
    setup_logging()
    app = FastAPI(
        title="PetBot AI Server",
        description="AI Chatbot Server for Pet Social Network",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Rate Limiting middleware
    app.add_middleware(RateLimitMiddleware)

    # Add custom identity validation middleware
    app.add_middleware(AuthMiddleware)

    # Include root routing prefixes
    app.include_router(api_router, prefix="/api")

    # Global Exception Handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle standard ValueError exceptions, returning 400 Bad Request.

        Args:
            request: The incoming HTTP request.
            exc: The caught ValueError exception.

        Returns:
            JSONResponse with status code 400.
        """
        logger.warning("ValueError intercepted: %s (Path: %s)", exc, request.url.path)
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unhandled system level exceptions, returning 500.

        Args:
            request: The incoming HTTP request.
            exc: The caught Exception.

        Returns:
            JSONResponse with status code 500.
        """
        logger.error(
            "Unhandled exception occurred at %s: %s",
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Lỗi hệ thống bất ngờ. Vui lòng thử lại sau."},
        )

    logger.info("FastAPI application factory compiled successfully.")
    return app
