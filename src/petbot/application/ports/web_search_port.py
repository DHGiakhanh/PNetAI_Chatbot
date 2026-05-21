from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IWebSearchTool(ABC):
    """Port for web search tools like Tavily."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform a search and return a list of result metadata (title/url/snippet)."""

    @abstractmethod
    async def fetch(self, url: str, timeout: Optional[float] = None) -> str:
        """Fetch full text content for a URL."""


__all__ = ["IWebSearchTool"]
