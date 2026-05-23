"""Web search tool port interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WebSearchResult:
    """Standardized web search result."""

    title: str
    url: str
    content: str
    score: float = 1.0


class IWebSearchTool(ABC):
    """Port interface for web search tools.

    Implementations:
        - TavilyWebSearchTool
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> list[WebSearchResult]:
        """Search the web for information.

        Args:
            query: The search query string.
            max_results: Maximum number of results.
            search_depth: 'basic' or 'advanced'.

        Returns:
            List of WebSearchResult objects.
        """
        ...
