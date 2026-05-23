"""Qdrant vector database client singleton."""

from __future__ import annotations

import logging
from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

VECTOR_DIM = 1536
DISTANCE_METRIC = models.Distance.COSINE


class QdrantClientManager:
    """Async Qdrant client wrapper."""

    def __init__(self, host: str, port: int, collection: str) -> None:
        self._host = host
        self._port = port
        self._collection = collection
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        """Return the underlying Qdrant async client (lazy init)."""
        if self._client is None:
            self._client = AsyncQdrantClient(host=self._host, port=self._port)
            logger.info("QdrantClient connected to %s:%d", self._host, self._port)
        return self._client

    @property
    def collection_name(self) -> str:
        """Return the configured collection name."""
        return self._collection

    async def ensure_collection_exists(self) -> None:
        """Create the collection if it does not already exist."""
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]

        if self._collection not in names:
            await self.client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIM,
                    distance=DISTANCE_METRIC,
                ),
            )
            logger.info(
                "Created Qdrant collection '%s' (dim=%d, metric=%s)",
                self._collection,
                VECTOR_DIM,
                DISTANCE_METRIC,
            )
        else:
            logger.info("Qdrant collection '%s' already exists", self._collection)

    async def ping(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the Qdrant connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None


@lru_cache
def get_qdrant_client() -> QdrantClientManager:
    """Return a cached QdrantClientManager singleton."""
    from pnetai_chatbot.infrastructure.config.settings import get_settings

    settings = get_settings()
    return QdrantClientManager(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
