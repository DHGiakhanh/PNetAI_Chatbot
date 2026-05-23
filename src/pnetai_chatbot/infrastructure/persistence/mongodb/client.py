"""MongoDB client singletons for Chat DB and Website DB.

Provides two separate Motor clients:
  - ChatClient: petbot's own DB (sessions, messages) — read/write
  - WebsiteClient: existing website DB (products, pets, etc.) — read-only
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MongoChatClient:
    """Async MongoDB client for the chatbot's own database.

    Manages sessions and message history.
    """

    def __init__(self, uri: str) -> None:
        self._uri = uri
        self._client: AsyncIOMotorClient | None = None

    @property
    def client(self) -> AsyncIOMotorClient:
        """Return the underlying Motor client (lazy init)."""
        if self._client is None:
            self._client = AsyncIOMotorClient(self._uri)
            logger.info("MongoChatClient connected to %s", self._safe_uri)
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the default database for this connection."""
        return self.client.get_default_database()

    @property
    def _safe_uri(self) -> str:
        """Return URI with credentials masked for logging."""
        return (
            self._uri.replace("://", "://***:***@")
            if "://" in self._uri and "@" in self._uri
            else self._uri
        )

    async def ping(self) -> bool:
        """Check if the MongoDB connection is alive."""
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None


class MongoWebsiteClient:
    """Async MongoDB client for the existing website database (read-only)."""

    def __init__(self, uri: str) -> None:
        self._uri = uri
        self._client: AsyncIOMotorClient | None = None

    @property
    def client(self) -> AsyncIOMotorClient:
        """Return the underlying Motor client (lazy init)."""
        if self._client is None:
            self._client = AsyncIOMotorClient(self._uri)
            logger.info("MongoWebsiteClient connected")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the default database for this connection."""
        return self.client.get_default_database()

    async def ping(self) -> bool:
        """Check if the MongoDB connection is alive."""
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None


@lru_cache
def get_chat_client() -> MongoChatClient:
    """Return a cached MongoChatClient singleton."""
    from pnetai_chatbot.infrastructure.config.settings import get_settings

    settings = get_settings()
    return MongoChatClient(settings.mongodb_chat_uri)


@lru_cache
def get_website_client() -> MongoWebsiteClient:
    """Return a cached MongoWebsiteClient singleton."""
    from pnetai_chatbot.infrastructure.config.settings import get_settings

    settings = get_settings()
    return MongoWebsiteClient(settings.mongodb_website_uri)
