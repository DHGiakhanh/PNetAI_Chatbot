"""Vector store port interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorSearchResult:
    """Standardized vector search result."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] | None = None


class IVectorStore(ABC):
    """Port interface for vector similarity search.

    Implementations:
        - QdrantVectorSearchTool
    """

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for documents similar to the query embedding.

        Args:
            query_embedding: The embedding vector of the user query.
            top_k: Number of top results to return.
            filters: Optional metadata filters.

        Returns:
            List of VectorSearchResult objects sorted by relevance.
        """
        ...
