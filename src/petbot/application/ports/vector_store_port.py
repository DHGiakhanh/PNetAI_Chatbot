from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IVectorStore(ABC):
    """Abstract vector store port (e.g., Qdrant)."""

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return vector search results with payloads and scores."""

    @abstractmethod
    async def upsert(self, collection_name: str, items: List[Dict[str, Any]]) -> None:
        """Upsert vector items (ids, vectors, payloads)."""

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> None:
        """Delete items by id from a collection."""


__all__ = ["IVectorStore"]
