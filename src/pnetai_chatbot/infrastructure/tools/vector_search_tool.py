"""Qdrant search implementation of IVectorStore."""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient

from pnetai_chatbot.application.ports.vector_store_port import (
    IVectorStore,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class QdrantVectorSearchTool(IVectorStore):
    """Qdrant similarity search implementation of IVectorStore."""

    def __init__(self, client: AsyncQdrantClient, collection_name: str) -> None:
        """Initialize QdrantVectorSearchTool.

        Args:
            client: The async Qdrant client instance.
            collection_name: The name of the collection to search.
        """
        self._client = client
        self._collection_name = collection_name

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Perform a similarity search in Qdrant.

        Args:
            query_embedding: The embedding vector of the search query.
            top_k: Number of top results to return.
            filters: Optional metadata filters.

        Returns:
            A list of VectorSearchResult objects.
        """
        logger.info(
            "Qdrant similarity search in collection '%s' (limit=%d)",
            self._collection_name,
            top_k,
        )
        try:
            results = await self._client.search(
                collection_name=self._collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=filters,
                with_payload=True,
            )
            return [
                VectorSearchResult(
                    id=str(r.id),
                    content=r.payload.get("content", "") if r.payload else "",
                    score=float(r.score),
                    metadata=dict(r.payload) if r.payload else None,
                )
                for r in results
            ]
        except Exception as e:
            logger.error("Qdrant similarity search failed: %s", e)
            raise e
