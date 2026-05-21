from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IMongoQueryExecutor(ABC):
    """Port for executing generated MongoDB queries and providing schema context."""

    @abstractmethod
    async def execute_generated_query(
        self,
        collection: str,
        filter_query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Execute a generated MongoDB filter/projection and return documents."""

    @abstractmethod
    async def get_schema_context(self, collection: str) -> str:
        """Return a short textual description of the collection schema for prompt context."""


__all__ = ["IMongoQueryExecutor"]
