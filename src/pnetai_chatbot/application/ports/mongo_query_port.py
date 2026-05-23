"""MongoDB query executor port interface."""

from abc import ABC, abstractmethod
from typing import Any


class IMongoQueryExecutor(ABC):
    """Port interface for executing MongoDB queries against the website database.

    Reads from the existing website MongoDB (read-only).
    """

    @abstractmethod
    async def execute_generated_query(
        self,
        collection: str,
        filter_query: dict[str, Any],
        projection: dict[str, int] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Execute a generated query against the website MongoDB.

        Args:
            collection: Target collection name.
            filter_query: MongoDB filter document.
            projection: Optional field projection.
            limit: Maximum documents to return.

        Returns:
            List of result documents.
        """
        ...

    @abstractmethod
    async def get_schema_context(self, collection: str) -> str:
        """Get the schema description for a collection.

        Used to inject schema info into LLM prompts for query generation.

        Args:
            collection: Collection name.

        Returns:
            Human-readable schema description string.
        """
        ...
